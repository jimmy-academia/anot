#!/usr/bin/env python3
"""Hierarchical ReAct Phase 2 - Smart lazy evaluation.

Key design principles:
1. Main agent checks HARD conditions first, filters items before spawning
2. Item agents check review METADATA (stars, dates, user_id) before spawning
3. Review agents only for TEXT understanding (keywords, sentiment)
4. Social queries: filter reviews by friend connections first

Architecture:
  Main Agent: hard filtering → spawn only for soft conditions
    └── Item Agent: metadata checks → spawn only for text analysis
          └── Review Agent: text search/sentiment (leaf)
"""

import re
import json
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field

from utils.llm import call_llm_async


# =============================================================================
# Configuration
# =============================================================================

MAX_DEPTH = 3  # 0=main, 1=item, 2=review
MAX_ITERATIONS = {0: 25, 1: 12, 2: 6}
SCOPE_NAMES = {0: "main", 1: "item", 2: "review"}


# =============================================================================
# Shared State
# =============================================================================

@dataclass
class SharedState:
    """Thread-safe shared state for step collection."""
    steps: List[Tuple[str, str]] = field(default_factory=list)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def add_step(self, step_id: str, prompt: str):
        async with self._lock:
            self.steps.append((step_id, prompt))

    async def get_steps(self) -> List[Tuple[str, str]]:
        async with self._lock:
            return list(self.steps)


@dataclass
class AgentContext:
    """Shared context for agent hierarchy."""
    lwt_seed: str
    conditions: List[dict]
    logical_structure: str
    items: Dict[str, dict]
    request_id: str
    shared_state: SharedState
    friends_1hop: set = field(default_factory=set)  # Direct friends
    friends_2hop: set = field(default_factory=set)  # Friends of friends
    debug_callback: Optional[callable] = None
    log_callback: Optional[callable] = None


# =============================================================================
# Condition Classification
# =============================================================================

def classify_conditions(conditions: List[dict]) -> dict:
    """Classify conditions into HARD, SOFT_META, SOFT_TEXT, SOCIAL."""
    result = {
        'hard': [],       # Attribute checks
        'soft_meta': [],  # Review metadata (dates, stars)
        'soft_text': [],  # Review text analysis
        'social': [],     # Friend-based filtering
    }

    for c in conditions:
        ctype = c.get('original_type', c.get('type', ''))
        path = c.get('path', '').lower()
        desc = c.get('description', '').lower()

        if ctype == 'SOCIAL' or 'friend' in desc or 'social' in desc:
            result['social'].append(c)
        elif 'review' in path or ctype == 'REVIEW':
            # Distinguish metadata vs text
            if any(kw in desc for kw in ['since', 'recent', 'date', '2020', '2021', '2022', '2023', '2024']):
                result['soft_meta'].append(c)
            elif any(kw in desc for kw in ['star', 'rating', 'score']):
                result['soft_meta'].append(c)
            else:
                result['soft_text'].append(c)
        elif 'hour' in path:
            result['soft_meta'].append(c)
        else:
            result['hard'].append(c)

    return result


# =============================================================================
# System Prompts
# =============================================================================

def get_main_prompt(n_items: int, cond_class: dict, items_summary: str) -> str:
    """Build main agent prompt with hard filtering capability."""
    hard_conds = "; ".join([f"{c.get('path', '')}={c.get('expected', c.get('description', ''))}"
                            for c in cond_class['hard']]) or "none"
    has_soft = bool(cond_class['soft_meta'] or cond_class['soft_text'] or cond_class['social'])

    return f"""## Task: Rank {n_items} items. Check HARD conditions first to filter.

HARD conditions: {hard_conds}
Has SOFT conditions: {has_soft}

Items summary:
{items_summary}

## Your job:
1. Use check_hard(N) to verify item N passes ALL hard conditions
2. Items that FAIL hard → skip (don't spawn)
3. Items that PASS hard {"→ spawn(N) for soft evaluation" if has_soft else "→ record score"}
4. After all checks: {"wait_all() then emit final ranking" if has_soft else "emit final ranking based on hard scores"}

Tools:
- check_hard(N) → check if item N passes hard conditions, returns pass/fail
- skip(N, reason) → mark item N as filtered out
- spawn(N) → spawn item agent for soft evaluation (only if passed hard)
- wait_all() → wait for item agents
- emit("final", "...") → emit final ranking step
- done() → finish

Example:
Action: check_hard(1)
Obs: check_hard(1): PASS (3/3 hard conditions)
Action: spawn(1)
Action: check_hard(2)
Obs: check_hard(2): FAIL (GoodForKids=false, need true)
Action: skip(2, "failed hard")
Action: check_hard(3)
Obs: check_hard(3): PASS (3/3 hard conditions)
Action: spawn(3)
...
Action: wait_all()
Obs: wait_all: 2 items completed: 1,3
Obs: Use in emit: {{(c1_eval)}} {{(c3_eval)}}
Action: emit("final", "Parse scores and rank. {{(c1_eval)}} {{(c3_eval)}}. Return top 5 IDs sorted by score descending.")
Action: done()

BEGIN:"""


def get_item_prompt(item_id: str, item: dict, cond_class: dict, friends_1hop: set, friends_2hop: set) -> str:
    """Build item agent prompt with metadata-first checking."""
    schema = {
        "name": item.get("name"),
        "stars": item.get("stars"),
        "n_reviews": len(item.get("reviews", [])),
    }

    # Build review metadata summary
    reviews = item.get("reviews", [])
    review_meta = []
    for i, r in enumerate(reviews[:10]):
        date = r.get('date', 'unknown')[:10]
        stars = r.get('stars', '?')
        user = r.get('user', {})
        user_id = user.get('user_id', r.get('user_id', 'unknown'))
        # Check friend status
        friend_status = ""
        if user_id in friends_1hop:
            friend_status = " [1-hop]"
        elif user_id in friends_2hop:
            friend_status = " [2-hop]"
        review_meta.append(f"R{i}: {date}, {stars}★, user={user_id[:8]}...{friend_status}")

    meta_str = "\n".join(review_meta) if review_meta else "no reviews"

    # Condition descriptions
    soft_meta = "; ".join([c.get('description', '') for c in cond_class['soft_meta']]) or "none"
    soft_text = "; ".join([c.get('description', '') for c in cond_class['soft_text']]) or "none"
    social = "; ".join([c.get('description', '') for c in cond_class['social']]) or "none"

    has_text_conds = bool(cond_class['soft_text'])
    has_social = bool(cond_class['social'])

    return f"""## Item {item_id}: {item.get('name', 'Unknown')}
Schema: {json.dumps(schema)}

Review metadata:
{meta_str}

## Conditions to check:
- META (dates/stars): {soft_meta}
- TEXT (need review content): {soft_text}
- SOCIAL (friend reviews): {social}

## Your job: Check META conditions first, only spawn review agents for TEXT conditions.

Tools:
- check_date(R, ">=2020") → check if review R is from 2020+
- check_stars(R, ">=4") → check if review R has 4+ stars
- check_friend(R) → check if review R is from 1-hop or 2-hop friend
- spawn(R) → spawn review agent for TEXT analysis (only if needed)
- wait_all() → wait for review agents
- emit("eval", "{item_id}:score") → emit item score
- done() → finish

Strategy:
1. For META conditions: use check_date/check_stars directly
2. For SOCIAL: use check_friend to filter, only spawn for friend reviews
3. For TEXT: spawn review agents only for reviews that pass meta/social filters
4. Emit score: "hard=PASS,meta=X/Y,text=A/B" or just counts

Example (with text conditions):
Action: check_date(0, ">=2020")
Obs: check_date(R0): PASS (2021-03-15)
Action: check_friend(0)
Obs: check_friend(R0): NOT_FRIEND
Action: check_date(1, ">=2020")
Obs: check_date(R1): PASS (2022-01-10)
Action: check_friend(1)
Obs: check_friend(R1): 1-HOP
Action: spawn(1)  # Only spawn for friend's review
Action: wait_all()
Obs: wait_all: 1 matched
Action: emit("eval", "{item_id}:meta=2,text=1")
Action: done()

{"" if has_text_conds else "No TEXT conditions - just check META and emit score directly."}

BEGIN:"""


def get_review_prompt(review_id: str, parent_id: str, text: str, cond_class: dict) -> str:
    """Build review agent prompt for text analysis."""
    text_preview = text[:600] + "..." if len(text) > 600 else text
    text_conds = "; ".join([c.get('description', '') for c in cond_class['soft_text']]) or "general relevance"

    return f"""## Review {review_id} for Item {parent_id}
Text: {text_preview}

## Looking for: {text_conds}

## Your job: Search text for relevant content. Emit if found, skip if not.

Tools:
- search("keyword") → find keyword in text, returns context if found
- emit("match", "description") → mark as relevant
- skip("reason") → mark as not relevant
- done() → finish

Example:
Action: search("wifi")
Obs: search(wifi): FOUND @123 "...the wifi here is excellent and fast..."
Thought: Found positive wifi mention
Action: emit("match", "wifi mentioned positively")
Action: done()

BEGIN:"""


SYSTEM_PROMPTS = {
    0: """You filter items by HARD conditions, then spawn for SOFT evaluation.
Use check_hard(N) before spawning. Skip items that fail hard conditions.""",

    1: """You evaluate item's SOFT conditions using review metadata first.
Only spawn review agents for TEXT-based conditions that need content analysis.""",

    2: """You analyze review text for specific content.
Search for keywords, assess sentiment, then emit or skip."""
}


# =============================================================================
# ReActAgent
# =============================================================================

class ReActAgent:
    """Recursive ReAct agent with smart lazy evaluation."""

    def __init__(
        self,
        agent_id: str,
        depth: int,
        context: AgentContext,
        scope_data: Any,
        parent_id: str = "",
        cond_class: dict = None,
    ):
        self.agent_id = agent_id
        self.depth = depth
        self.context = context
        self.scope_data = scope_data
        self.parent_id = parent_id
        self.cond_class = cond_class or classify_conditions(context.conditions)

        self.sub_tasks: Dict[str, asyncio.Task] = {}
        self.skipped = False
        self.skip_reason = ""
        self.hard_results: Dict[str, bool] = {}  # Track hard check results

    def _debug(self, msg: str):
        if self.context.debug_callback:
            scope = SCOPE_NAMES.get(self.depth, f"d{self.depth}")
            self.context.debug_callback(2, "P2H", f"[{scope}:{self.agent_id}] {msg}")

    def _log_llm(self, step: str, prompt: str, response: str):
        if self.context.log_callback:
            self.context.log_callback("P2H", f"{self.agent_id}_{step}", prompt, response)

    def _can_spawn(self) -> bool:
        return self.depth < MAX_DEPTH - 1

    def _get_nested(self, data: dict, path: str) -> Any:
        parts = path.replace('[', '.').replace(']', '').split('.')
        val = data
        for part in parts:
            if not part:
                continue
            if isinstance(val, dict):
                val = val.get(part)
            elif isinstance(val, list) and part.isdigit():
                idx = int(part)
                val = val[idx] if 0 <= idx < len(val) else None
            else:
                return None
            if val is None:
                return None
        return val

    def _step_prefix(self) -> str:
        if self.depth == 1:
            return f"c{self.agent_id}_"
        elif self.depth == 2:
            return f"r{self.parent_id}_{self.agent_id}_"
        return ""

    # -------------------------------------------------------------------------
    # Hard Condition Checking (Main Agent)
    # -------------------------------------------------------------------------

    def _check_hard_conditions(self, item_id: str) -> Tuple[bool, int, int, str]:
        """Check all hard conditions for an item. Returns (passed, matches, total, reason)."""
        item = self.scope_data.get(item_id, {})
        if not item:
            return False, 0, 0, "item not found"

        matches = 0
        total = len(self.cond_class['hard'])
        fail_reason = ""

        for cond in self.cond_class['hard']:
            path = cond.get('path', '')
            expected = cond.get('expected', cond.get('description', ''))

            actual = self._get_nested(item, path)

            # Check match
            matched = False
            if actual is not None:
                # Handle various comparison types
                if isinstance(expected, bool):
                    matched = (actual == expected)
                elif str(expected).lower() in ['true', 'false']:
                    matched = (str(actual).lower() == str(expected).lower())
                elif str(expected).lower() == 'none':
                    matched = (actual is None or str(actual).lower() == 'none')
                else:
                    matched = (str(actual).lower() == str(expected).lower())

            if matched:
                matches += 1
            elif not fail_reason:
                fail_reason = f"{path}={actual}, need {expected}"

        passed = (matches == total) if total > 0 else True
        return passed, matches, total, fail_reason

    # -------------------------------------------------------------------------
    # Prompts
    # -------------------------------------------------------------------------

    def _build_prompt(self) -> str:
        if self.depth == 0:
            # Main agent - build items summary
            items_summary = []
            for item_id, item in sorted(self.scope_data.items(), key=lambda x: int(x[0])):
                name = item.get('name', 'Unknown')[:25]
                attrs = item.get('attributes', {})
                # Show key attributes relevant to hard conditions
                attr_preview = []
                for cond in self.cond_class['hard'][:3]:
                    path = cond.get('path', '')
                    val = self._get_nested(item, path)
                    if val is not None:
                        short_path = path.split('.')[-1][:15]
                        attr_preview.append(f"{short_path}={val}")
                attr_str = ", ".join(attr_preview) if attr_preview else "..."
                items_summary.append(f"{item_id}: {name} ({attr_str})")

            return get_main_prompt(
                len(self.scope_data),
                self.cond_class,
                "\n".join(items_summary[:15]) + ("\n..." if len(items_summary) > 15 else "")
            )

        elif self.depth == 1:
            return get_item_prompt(
                self.agent_id,
                self.scope_data,
                self.cond_class,
                self.context.friends_1hop,
                self.context.friends_2hop
            )

        else:
            text = self.scope_data.get('text', '')
            return get_review_prompt(
                self.agent_id,
                self.parent_id,
                text,
                self.cond_class
            )

    # -------------------------------------------------------------------------
    # Tool Execution
    # -------------------------------------------------------------------------

    async def _exec_tools(self, response: str) -> Tuple[str, bool]:
        """Execute tools, return (observation, is_done)."""
        obs = []

        # === Depth 0: Main agent - hard checking ===
        if self.depth == 0:
            # check_hard(N)
            for m in re.finditer(r'check_hard\((\d+)\)', response):
                item_id = m.group(1)
                passed, matches, total, reason = self._check_hard_conditions(item_id)
                self.hard_results[item_id] = passed
                if passed:
                    obs.append(f"check_hard({item_id}): PASS ({matches}/{total} hard conditions)")
                else:
                    obs.append(f"check_hard({item_id}): FAIL ({reason})")

            # skip(N, reason)
            for m in re.finditer(r'skip\((\d+),\s*"([^"]+)"\)', response):
                item_id = m.group(1)
                reason = m.group(2)
                self._debug(f"skipped item {item_id}: {reason}")
                obs.append(f"skip({item_id}): marked as filtered")

        # === Depth 1: Item agent - metadata checking ===
        if self.depth == 1:
            reviews = self.scope_data.get('reviews', [])

            # check_date(R, ">=2020")
            for m in re.finditer(r'check_date\((\d+),\s*"([^"]+)"\)', response):
                r_idx = int(m.group(1))
                date_cond = m.group(2)
                if r_idx < len(reviews):
                    review = reviews[r_idx]
                    date = review.get('date', '')[:10]
                    # Simple year extraction
                    year = int(date[:4]) if date and len(date) >= 4 else 0
                    # Parse condition like ">=2020"
                    if '>=' in date_cond:
                        threshold = int(date_cond.replace('>=', ''))
                        passed = year >= threshold
                    else:
                        passed = date_cond in date
                    status = "PASS" if passed else "FAIL"
                    obs.append(f"check_date(R{r_idx}): {status} ({date})")
                else:
                    obs.append(f"check_date(R{r_idx}): invalid index")

            # check_stars(R, ">=4")
            for m in re.finditer(r'check_stars\((\d+),\s*"([^"]+)"\)', response):
                r_idx = int(m.group(1))
                star_cond = m.group(2)
                if r_idx < len(reviews):
                    review = reviews[r_idx]
                    stars = review.get('stars', 0)
                    if '>=' in star_cond:
                        threshold = float(star_cond.replace('>=', ''))
                        passed = stars >= threshold
                    else:
                        passed = stars == float(star_cond)
                    status = "PASS" if passed else "FAIL"
                    obs.append(f"check_stars(R{r_idx}): {status} ({stars}★)")
                else:
                    obs.append(f"check_stars(R{r_idx}): invalid index")

            # check_friend(R)
            for m in re.finditer(r'check_friend\((\d+)\)', response):
                r_idx = int(m.group(1))
                if r_idx < len(reviews):
                    review = reviews[r_idx]
                    user = review.get('user', {})
                    user_id = user.get('user_id', review.get('user_id', ''))
                    if user_id in self.context.friends_1hop:
                        obs.append(f"check_friend(R{r_idx}): 1-HOP friend")
                    elif user_id in self.context.friends_2hop:
                        obs.append(f"check_friend(R{r_idx}): 2-HOP friend")
                    else:
                        obs.append(f"check_friend(R{r_idx}): NOT_FRIEND")
                else:
                    obs.append(f"check_friend(R{r_idx}): invalid index")

            # list_reviews()
            if "list_reviews()" in response:
                info = []
                for i, r in enumerate(reviews[:10]):
                    date = r.get('date', '')[:10]
                    stars = r.get('stars', '?')
                    info.append(f"R{i}:{date},{stars}★")
                obs.append(f"reviews({len(reviews)}): {', '.join(info)}")

        # === Depth 2: Review agent - text search ===
        if self.depth == 2:
            text = self.scope_data.get('text', '')

            for m in re.finditer(r'search\("([^"]+)"\)', response):
                kw = m.group(1).lower()
                if kw in text.lower():
                    idx = text.lower().index(kw)
                    start = max(0, idx - 40)
                    end = min(len(text), idx + len(kw) + 80)
                    snippet = text[start:end]
                    obs.append(f'search({kw}): FOUND @{idx} "{snippet}"')
                else:
                    obs.append(f"search({kw}): NOT FOUND")

        # === Common: spawn ===
        for m in re.finditer(r'spawn\((\d+)\)', response):
            sub_id = m.group(1)
            if not self._can_spawn():
                obs.append(f"spawn({sub_id}): ERROR max depth")
                continue
            if sub_id in self.sub_tasks:
                obs.append(f"spawn({sub_id}): already running")
                continue

            # Get sub-data
            if self.depth == 0:
                # Main spawning item agent
                sub_data = self.scope_data.get(sub_id)
            else:
                # Item spawning review agent
                revs = self.scope_data.get('reviews', [])
                idx = int(sub_id)
                sub_data = revs[idx] if idx < len(revs) else None

            if not sub_data:
                obs.append(f"spawn({sub_id}): invalid")
                continue

            sub = ReActAgent(
                sub_id, self.depth + 1, self.context, sub_data,
                self.agent_id, self.cond_class
            )
            self.sub_tasks[sub_id] = asyncio.create_task(sub.run())
            obs.append(f"spawn({sub_id}): started")
            self._debug(f"spawned {sub_id}")

        # === Common: wait_all ===
        if "wait_all()" in response:
            if self.sub_tasks:
                self._debug(f"waiting for {len(self.sub_tasks)} sub-agents")
                # Gather with ID tracking
                task_ids = list(self.sub_tasks.keys())
                results = await asyncio.gather(*self.sub_tasks.values(), return_exceptions=True)
                matched_ids = []
                skipped_ids = []
                error_ids = []
                for tid, result in zip(task_ids, results):
                    if result is True:
                        matched_ids.append(tid)
                    elif result is False:
                        skipped_ids.append(tid)
                    else:
                        error_ids.append(tid)
                total = len(self.sub_tasks)

                # For main agent (depth 0): report spawned item IDs
                if self.depth == 0 and matched_ids:
                    eval_refs = " ".join([f"{{{{(c{tid}_eval)}}}}" for tid in sorted(matched_ids, key=int)])
                    obs.append(f"wait_all: {len(matched_ids)} items completed: {','.join(matched_ids)}")
                    obs.append(f"Use in emit: {eval_refs}")
                else:
                    obs.append(f"wait_all: {len(matched_ids)} matched, {len(skipped_ids)} skipped, {len(error_ids)} errors (of {total})")
                self.sub_tasks.clear()
            else:
                obs.append("wait_all: no pending agents")

        # === Common: emit ===
        for m in re.finditer(r'emit\("([^"]+)",\s*"((?:[^"\\]|\\.)*)"\)', response, re.DOTALL):
            step_id = m.group(1)
            prompt = m.group(2).replace('\\"', '"').replace('\\n', '\n')
            full_id = self._step_prefix() + step_id
            await self.context.shared_state.add_step(full_id, prompt)
            obs.append(f"emit({step_id}): added as {full_id}")
            self._debug(f"emitted {full_id}")

        # === Common: skip ===
        if self.depth > 0:  # Item/review agent skip
            for m in re.finditer(r'skip\("([^"]+)"\)', response):
                self.skipped = True
                self.skip_reason = m.group(1)
                self._debug(f"skipped: {self.skip_reason}")
                return f"skipped: {self.skip_reason}", True

        # === Common: done ===
        if "done()" in response.lower():
            if self.sub_tasks:
                self._debug(f"done() - waiting for {len(self.sub_tasks)} remaining")
                await asyncio.gather(*self.sub_tasks.values(), return_exceptions=True)
                self.sub_tasks.clear()
            return "done", True

        if not obs:
            if self.depth == 0:
                obs.append("tools: check_hard, skip, spawn, wait_all, emit, done")
            elif self.depth == 1:
                obs.append("tools: check_date, check_stars, check_friend, list_reviews, spawn, wait_all, emit, done")
            else:
                obs.append("tools: search, emit, skip, done")

        return "\n".join(obs), False

    # -------------------------------------------------------------------------
    # Run
    # -------------------------------------------------------------------------

    async def run(self) -> bool:
        """Run agent. Returns True if not skipped."""
        max_iter = MAX_ITERATIONS.get(self.depth, 10)
        conv = [self._build_prompt()]

        for i in range(max_iter):
            self._debug(f"iter {i+1}/{max_iter}")

            prompt = "\n".join(conv)
            resp = await call_llm_async(
                prompt,
                system=SYSTEM_PROMPTS.get(self.depth, ""),
                role="planner",
                context={"method": "anot", "phase": "2h", "depth": self.depth, "id": self.agent_id}
            )
            self._log_llm(f"i{i}", prompt, resp)

            if not resp.strip():
                break

            obs, done = await self._exec_tools(resp)

            if self.skipped or done:
                break

            conv.append(f"\n{resp}\nObs: {obs}\n")

        return not self.skipped


# =============================================================================
# Entry Point
# =============================================================================

async def run_hierarchical_phase2(
    lwt_seed: str,
    resolved_conditions: List[dict],
    logical_structure: str,
    items: Dict[str, dict],
    request_id: str = "R01",
    debug_callback: callable = None,
    log_callback: callable = None,
    friends_1hop: set = None,
    friends_2hop: set = None,
) -> List[Tuple[str, str]]:
    """Run hierarchical Phase 2. Returns (step_id, prompt) list."""

    shared = SharedState()
    context = AgentContext(
        lwt_seed=lwt_seed,
        conditions=resolved_conditions,
        logical_structure=logical_structure,
        items=items,
        request_id=request_id,
        shared_state=shared,
        friends_1hop=friends_1hop or set(),
        friends_2hop=friends_2hop or set(),
        debug_callback=debug_callback,
        log_callback=log_callback,
    )

    # Run main agent
    main_agent = ReActAgent("main", 0, context, items)
    await main_agent.run()

    return await shared.get_steps()
