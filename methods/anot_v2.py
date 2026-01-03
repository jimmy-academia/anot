#!/usr/bin/env python3
"""ANoT v2 - Condition-Based Scoring.

Instead of subjective 0-10 scores, extract conditions from user request
and check each restaurant with binary YES/NO per condition.

Two-phase architecture:
1. CONDITION EXTRACTION: Parse user request into structured conditions
2. CONDITION CHECKING: For each restaurant, verify YES/NO per condition
3. RANKING: Sort by number of conditions satisfied
"""

import os
import sys
import json
import re
import time
import asyncio
from typing import Optional, Dict, List, Tuple

from .base import BaseMethod
from utils.llm import call_llm, call_llm_async
from utils.usage import get_usage_tracker

# Debug level: 0=off, 1=summary, 2=verbose, 3=full
ANOT_DEBUG = int(os.environ.get("ANOT_DEBUG", "0"))


# =============================================================================
# Prompts
# =============================================================================

CONDITION_EXTRACT_PROMPT = """Extract search conditions from this user request.

[USER REQUEST]
{context}

[AVAILABLE ATTRIBUTES]
DriveThru, WiFi, NoiseLevel, GoodForKids, OutdoorSeating, Alcohol,
DogsAllowed, BikeParking, RestaurantsPriceRange2, Ambience, HasTV,
RestaurantsReservations, RestaurantsGoodForGroups, RestaurantsTakeOut,
RestaurantsDelivery, BusinessAcceptsCreditCards, WheelchairAccessible,
CoatCheck, BYOB, GoodForMeal (breakfast, brunch, lunch, dinner, latenight)

[OUTPUT FORMAT]
List each condition on its own line:
1. type:field = value (reason from request)
2. type:field = value (reason from request)
...

Types:
- attribute: Check restaurant attribute (e.g., attribute:DriveThru = True)
- review: Search review text for keyword (e.g., review:matcha latte)
- hours: Check operating hours (e.g., hours:Monday:7:00)

Value formats:
- Boolean: True or False
- String: exact value like "u'quiet'" or "u'free'"
- Price: 1 (cheap), 2 (mid), 3 (upscale), 4 (expensive)
- Ambience/Meal: contains pattern like "'trendy': True"

Extract ALL conditions mentioned in the request (typically 2-5).
"""

CONDITION_CHECK_PROMPT = """Check if this restaurant matches the conditions.

[RESTAURANT: {name}]
Attributes:
{attributes}

Sample Reviews:
{reviews}

[CONDITIONS TO CHECK]
{conditions}

For EACH condition, output YES or NO on its own line:
1. YES or NO
2. YES or NO
...

Be strict: only YES if the condition is clearly satisfied.
"""


# =============================================================================
# Helper Functions
# =============================================================================

def parse_conditions(response: str) -> List[Dict]:
    """Parse extracted conditions from LLM response.

    Expected format:
    1. attribute:DriveThru = True (drive-thru mentioned)
    2. attribute:GoodForKids = True (kid-friendly)
    3. review:matcha (matcha latte)
    """
    conditions = []
    for line in response.strip().split('\n'):
        line = line.strip()
        if not line or not line[0].isdigit():
            continue

        # Remove leading number and dot
        line = re.sub(r'^\d+\.\s*', '', line)

        # Parse type:field = value (reason)
        match = re.match(r'(\w+):(\S+)\s*=\s*([^(]+?)(?:\s*\(|$)', line)
        if match:
            ctype, field, value = match.groups()
            conditions.append({
                'type': ctype.strip(),
                'field': field.strip(),
                'value': value.strip(),
            })
            continue

        # Parse review:keyword format (no = sign)
        match = re.match(r'review:(.+?)(?:\s*\(|$)', line)
        if match:
            conditions.append({
                'type': 'review',
                'field': 'text',
                'value': match.group(1).strip(),
            })

    return conditions


def parse_condition_checks(response: str, n_conditions: int) -> List[bool]:
    """Parse YES/NO responses for each condition.

    Returns list of booleans, one per condition.
    """
    results = []
    for line in response.strip().split('\n'):
        line = line.strip().upper()
        if 'YES' in line:
            results.append(True)
        elif 'NO' in line:
            results.append(False)

        if len(results) >= n_conditions:
            break

    # Pad with False if not enough responses
    while len(results) < n_conditions:
        results.append(False)

    return results


def format_attributes(attrs: dict) -> str:
    """Format attributes dict for prompt."""
    if not attrs:
        return "(no attributes)"

    lines = []
    for k, v in sorted(attrs.items()):
        if v and v != 'None':
            lines.append(f"  {k}: {v}")
    return '\n'.join(lines) if lines else "(no attributes)"


def format_reviews(reviews: list, max_reviews: int = 3) -> str:
    """Format reviews for prompt."""
    if not reviews:
        return "(no reviews)"

    texts = []
    for r in reviews[:max_reviews]:
        text = r.get('review', r.get('text', ''))[:200]
        if text:
            texts.append(f"  - {text}")
    return '\n'.join(texts) if texts else "(no reviews)"


# =============================================================================
# ANoT v2 Implementation
# =============================================================================

class ANoTv2(BaseMethod):
    """ANoT v2 - Condition-based scoring instead of subjective 0-10."""

    name = "anot_v2"

    def __init__(self, run_dir: str = None, defense: bool = False, verbose: bool = True, **kwargs):
        super().__init__(run_dir=run_dir, defense=defense, verbose=verbose, **kwargs)
        self._condition_cache = {}  # Cache extracted conditions per context

    def _debug(self, level: int, phase: str, msg: str, content: str = None):
        """Debug output."""
        if ANOT_DEBUG < level:
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] [{phase}] {msg}"
        print(log_line, file=sys.stderr, flush=True)

        if content and ANOT_DEBUG >= 3:
            content_preview = content[:500] + "..." if len(content) > 500 else content
            print(f"  >>> {content_preview}", file=sys.stderr, flush=True)

    # =========================================================================
    # Phase 1: Condition Extraction
    # =========================================================================

    def phase1_extract_conditions(self, context: str) -> List[Dict]:
        """Extract conditions from user request."""
        self._debug(1, "P1", f"Extracting conditions from: {context[:60]}...")

        # Check cache
        if context in self._condition_cache:
            cached = self._condition_cache[context]
            self._debug(1, "P1", f"Using cached conditions: {len(cached)} conditions")
            return cached

        prompt = CONDITION_EXTRACT_PROMPT.format(context=context)
        self._debug(3, "P1", "Extraction prompt:", prompt)

        response = call_llm(
            prompt,
            system="You are a precise condition extractor. Output only the numbered list.",
            role="extractor",
            context={"method": "anot_v2", "phase": 1}
        )

        self._debug(2, "P1", f"Raw response:", response)

        conditions = parse_conditions(response)
        self._debug(1, "P1", f"Extracted {len(conditions)} conditions: {conditions}")

        # Cache for reuse
        self._condition_cache[context] = conditions
        return conditions

    # =========================================================================
    # Phase 2: Condition Checking
    # =========================================================================

    def phase2_check_conditions(self, item: dict, conditions: List[Dict]) -> List[bool]:
        """Check if item satisfies each condition."""
        name = item.get('item_name', 'Unknown')
        attrs = item.get('attributes', {})
        reviews = item.get('reviews', item.get('item_data', []))

        # Format for prompt
        attrs_str = format_attributes(attrs)
        reviews_str = format_reviews(reviews)

        # Format conditions list
        cond_lines = []
        for i, c in enumerate(conditions, 1):
            if c['type'] == 'review':
                cond_lines.append(f"{i}. Reviews mention: {c['value']}")
            elif c['type'] == 'hours':
                cond_lines.append(f"{i}. Open at: {c['field']}:{c['value']}")
            else:
                cond_lines.append(f"{i}. {c['field']} = {c['value']}")

        prompt = CONDITION_CHECK_PROMPT.format(
            name=name,
            attributes=attrs_str,
            reviews=reviews_str,
            conditions='\n'.join(cond_lines)
        )

        self._debug(3, "P2", f"Check prompt for {name}:", prompt)

        response = call_llm(
            prompt,
            system="You are a strict condition checker. Answer only YES or NO for each condition.",
            role="checker",
            context={"method": "anot_v2", "phase": 2, "item": name}
        )

        self._debug(2, "P2", f"{name} raw response:", response)

        results = parse_condition_checks(response, len(conditions))
        match_count = sum(results)
        self._debug(1, "P2", f"{name}: {match_count}/{len(conditions)} conditions matched")

        return results

    async def phase2_check_conditions_async(self, item: dict, conditions: List[Dict]) -> Tuple[str, List[bool], int]:
        """Async version for parallel checking."""
        name = item.get('item_name', 'Unknown')
        attrs = item.get('attributes', {})
        reviews = item.get('reviews', item.get('item_data', []))

        attrs_str = format_attributes(attrs)
        reviews_str = format_reviews(reviews)

        cond_lines = []
        for i, c in enumerate(conditions, 1):
            if c['type'] == 'review':
                cond_lines.append(f"{i}. Reviews mention: {c['value']}")
            elif c['type'] == 'hours':
                cond_lines.append(f"{i}. Open at: {c['field']}:{c['value']}")
            else:
                cond_lines.append(f"{i}. {c['field']} = {c['value']}")

        prompt = CONDITION_CHECK_PROMPT.format(
            name=name,
            attributes=attrs_str,
            reviews=reviews_str,
            conditions='\n'.join(cond_lines)
        )

        response = await call_llm_async(
            prompt,
            system="You are a strict condition checker. Answer only YES or NO for each condition.",
            role="checker",
            context={"method": "anot_v2", "phase": 2, "item": name}
        )

        results = parse_condition_checks(response, len(conditions))
        match_count = sum(results)
        self._debug(1, "P2", f"{name}: {match_count}/{len(conditions)}")

        return name, results, match_count

    # =========================================================================
    # Main Entry Point
    # =========================================================================

    def evaluate_ranking(self, query, context: str, k: int = 5, request_id: str = "R00") -> str:
        """Ranking evaluation with condition-based scoring.

        Phase 1: Extract conditions from user request
        Phase 2: Check conditions for each restaurant (parallel)
        Phase 3: Rank by condition satisfaction count
        """
        self._debug(1, "MAIN", f"=== {request_id}: {context[:50]}... ===")

        # Parse items
        if isinstance(query, str):
            data = json.loads(query)
        else:
            data = query
        items = data.get('items', [data]) if isinstance(data, dict) else [data]

        self._debug(1, "MAIN", f"Evaluating {len(items)} items, returning top-{k}")

        # Phase 1: Extract conditions
        conditions = self.phase1_extract_conditions(context)

        if not conditions:
            self._debug(1, "P1", "WARNING: No conditions extracted, returning default order")
            return ", ".join(str(i+1) for i in range(min(k, len(items))))

        # Phase 2: Check conditions for each restaurant (parallel)
        async def check_all():
            tasks = [self.phase2_check_conditions_async(item, conditions) for item in items]
            return await asyncio.gather(*tasks)

        try:
            results = asyncio.run(check_all())
        except RuntimeError:
            # Already in async context, run sequentially
            results = []
            for item in items:
                checks = self.phase2_check_conditions(item, conditions)
                name = item.get('item_name', 'Unknown')
                results.append((name, checks, sum(checks)))

        # Phase 3: Rank by condition count (descending), then by original order
        ranked = []
        for idx, (name, checks, count) in enumerate(results):
            ranked.append((idx, count, name))

        # Sort by count descending, then by index ascending (stable)
        ranked.sort(key=lambda x: (-x[1], x[0]))

        top_k = [str(r[0] + 1) for r in ranked[:k]]  # 1-indexed

        # Debug output
        self._debug(1, "P3", f"Final ranking: {ranked[:k]}")
        self._debug(1, "MAIN", f"Result: {','.join(top_k)}")

        return ", ".join(top_k)

    def evaluate(self, query, context: str) -> int:
        """Single item evaluation (not used for ranking)."""
        return 0


# =============================================================================
# Factory
# =============================================================================

def create_method(run_dir: str = None, defense: bool = False, **kwargs):
    """Factory function to create ANoT v2 instance."""
    return ANoTv2(run_dir=run_dir, defense=defense, **kwargs)
