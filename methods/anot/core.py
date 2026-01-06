#!/usr/bin/env python3
"""ANoT - Adaptive Network of Thought (Enhanced).

Three-phase architecture:
1. PLANNING: Schema extraction + 3 LLM calls (conditions → pruning → skeleton)
2. EXPANSION: ReAct-like LWT expansion with tools
3. EXECUTION: Pure LWT execution with async DAG
"""

import os
import json
import re
import time
import asyncio
import threading
import traceback
from typing import Dict, List, Tuple

from rich.live import Live
from rich.table import Table
from rich.console import Console
from rich.text import Text

from ..base import BaseMethod
from utils.llm import call_llm, call_llm_async
from utils.parsing import parse_script, substitute_variables
from utils.usage import get_usage_tracker

from .prompts import SYSTEM_PROMPT, PHASE1_PROMPT, PHASE2_PROMPT, RANKING_TASK_COMPACT
from .helpers import build_execution_layers, format_items_compact, format_schema_compact, filter_items_for_ranking
from .tools import (
    tool_read, tool_lwt_list, tool_lwt_get,
    tool_lwt_set, tool_lwt_delete, tool_lwt_insert
)


class AdaptiveNetworkOfThought(BaseMethod):
    """Enhanced Adaptive Network of Thought - three-phase architecture."""

    name = "anot"

    def __init__(self, run_dir: str = None, defense: bool = False, verbose: bool = True, **kwargs):
        super().__init__(run_dir=run_dir, defense=defense, verbose=verbose, **kwargs)
        self._thread_local = threading.local()
        self._traces = {}
        self._traces_lock = threading.Lock()
        self._console = Console(force_terminal=True)
        self._live = None
        self._display_rows = {}
        self._display_lock = threading.RLock()
        self._display_title = ""
        self._display_stats = {"complete": 0, "total": 0, "tokens": 0, "cost": 0.0}
        self._last_display_update = 0
        self._errors = []  # Accumulated errors: (request_id, step_idx, error_msg)
        self._debug_log_file = None
        self._debug_log_path = None

        # Always open debug log file (append mode to avoid overwriting during scaling)
        if run_dir:
            self._debug_log_path = os.path.join(run_dir, "debug.log")
            try:
                self._debug_log_file = open(self._debug_log_path, "a", buffering=1)
                from datetime import datetime
                self._debug_log_file.write(f"\n=== ANoT Debug Log @ {datetime.now().isoformat()} ===\n")
                self._debug_log_file.flush()
            except Exception:
                pass  # Silent fail - debug log is optional

    def __del__(self):
        """Close debug log file on cleanup."""
        if hasattr(self, '_debug_log_file') and self._debug_log_file:
            try:
                self._debug_log_file.close()
            except Exception:
                pass

    # =========================================================================
    # Debug/Trace Methods
    # =========================================================================

    def _debug(self, level: int, phase: str, msg: str, content: str = None):
        """Write debug to file only (no terminal output)."""
        if not self._debug_log_file:
            return
        req_id = getattr(self._thread_local, 'request_id', 'R??')
        prefix = f"[{phase}:{req_id}]"
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] {prefix} {msg}"

        self._debug_log_file.write(log_line + "\n")
        if content:
            self._debug_log_file.write(f">>> {content}\n")
        self._debug_log_file.flush()

    def _init_trace(self, request_id: str, context: str):
        """Initialize trace for request."""
        trace = {
            "request_id": request_id,
            "context": context,
            "phase1": {"strategy": "", "message": "", "latency_ms": 0},
            "phase2": {"expanded_lwt": [], "react_iterations": 0, "latency_ms": 0},
            "phase3": {"step_results": {}, "top_k": [], "final_output": "", "latency_ms": 0},
        }
        with self._traces_lock:
            self._traces[request_id] = trace

    def _get_trace(self, request_id: str = None) -> dict:
        """Get trace for request."""
        rid = request_id or getattr(self._thread_local, 'request_id', None)
        if not rid:
            return None
        with self._traces_lock:
            return self._traces.get(rid)

    def _update_trace_step(self, idx: str, data: dict):
        """Thread-safe update of trace step result."""
        with self._traces_lock:
            req_id = getattr(self._thread_local, 'request_id', None)
            if req_id and req_id in self._traces:
                self._traces[req_id]["phase3"]["step_results"][idx] = data

    def _save_trace_incremental(self, request_id: str = None):
        """Save current trace to JSONL file incrementally."""
        trace = self._get_trace(request_id)
        if not trace or not self.run_dir:
            return

        trace_path = os.path.join(self.run_dir, "anot_trace.jsonl")
        try:
            with open(trace_path, "a") as f:
                f.write(json.dumps(trace) + "\n")
                f.flush()
        except Exception as e:
            self._debug(1, "TRACE", f"Failed to save trace: {e}")

    def _log_llm_call(self, phase: str, step: str, prompt: str, response: str):
        """Log LLM call details to debug file."""
        if not self._debug_log_file:
            return

        req_id = getattr(self._thread_local, 'request_id', 'R??')
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        self._debug_log_file.write(f"\n{'='*60}\n")
        self._debug_log_file.write(f"[{timestamp}] [{phase}:{req_id}] LLM Call: {step}\n")
        self._debug_log_file.write(f"{'='*60}\n")
        self._debug_log_file.write(f"PROMPT:\n{prompt}\n")
        self._debug_log_file.write(f"{'-'*40}\n")
        self._debug_log_file.write(f"RESPONSE:\n{response}\n")
        self._debug_log_file.write(f"{'='*60}\n\n")
        self._debug_log_file.flush()

    # =========================================================================
    # Cache Methods
    # =========================================================================

    def _get_cache(self) -> dict:
        """Get thread-local step results cache."""
        return getattr(self._thread_local, 'cache', {})

    def _set_cache(self, value: dict):
        """Set thread-local step results cache."""
        self._thread_local.cache = value

    def _cache_set(self, key: str, value):
        """Set value in thread-local cache."""
        cache = self._get_cache()
        cache[key] = value
        self._thread_local.cache = cache

    # =========================================================================
    # Display Methods
    # =========================================================================

    def start_display(self, title: str = "", total: int = 0, requests: list = None):
        """Start rich Live display."""
        self._display_title = title
        self._display_stats = {"complete": 0, "total": total, "tokens": 0, "cost": 0.0}
        self._display_rows = {}
        self._last_display_update = 0

        if requests:
            for req in requests:
                rid = req.get("id", req.get("text", "")[:20])
                ctx = req.get("context") or req.get("text", "")
                self._display_rows[rid] = {"context": ctx, "phase": "---", "status": "pending"}

        self._live = Live(
            self._render_table(),
            console=self._console,
            refresh_per_second=4,
            transient=False,
            vertical_overflow="visible",
        )
        self._live.start()

    def stop_display(self):
        """Stop rich Live display and print error summary if any."""
        if self._live:
            self._live.stop()
            self._live = None

        if self._errors:
            print(f"\n⚠️  {len(self._errors)} error(s) during execution:")
            for req_id, step_idx, msg in self._errors:
                print(f"  [{req_id}] Step {step_idx}: {msg}")
            self._errors.clear()

    def _update_display(self, request_id: str, phase: str, status: str, context: str = None):
        """Update display row for request."""
        with self._display_lock:
            was_complete = self._display_rows.get(request_id, {}).get("phase") == "✓"
            if request_id not in self._display_rows:
                self._display_rows[request_id] = {"context": context or "", "phase": phase, "status": status}
            else:
                self._display_rows[request_id]["phase"] = phase
                self._display_rows[request_id]["status"] = status
                if context:
                    self._display_rows[request_id]["context"] = context

            if phase == "✓" and not was_complete:
                self._display_stats["complete"] += 1
                summary = get_usage_tracker().get_summary()
                self._display_stats["tokens"] = summary.get("total_tokens", 0)
                self._display_stats["cost"] = summary.get("total_cost_usd", 0.0)

            if self._live:
                now = time.time()
                if now - self._last_display_update >= 0.1:
                    self._live.update(self._render_table())
                    self._last_display_update = now

    def _render_table(self) -> Table:
        """Build current display table with 4-column layout for compact view."""
        # Calculate dynamic widths based on console width
        console_width = self._console.width or 120
        # With padding=0:
        # Fixed per group: Req(4) + Ph(2) = 6, times 4 groups = 24
        # Plus 3 separators (width=1 each) = 3, total fixed = 27
        # Remaining split: Query gets 2x, St gets 1x (ratio 2:1)
        available = max(40, console_width - 27)  # minimum 40 for flexible
        # 4 groups * (2 + 1) = 12 ratio units
        unit = available // 12
        query_width = max(10, unit * 2)
        status_width = max(6, unit)

        table = Table(title=self._display_title, box=None, padding=0, collapse_padding=True)

        # 4 repeated column groups: Req, Query, Ph, St (with separator)
        for i in range(4):
            table.add_column("Req", style="cyan", width=4, no_wrap=True)
            table.add_column("Query", style="dim", width=query_width, no_wrap=True)
            table.add_column("Ph", style="bold", width=2, justify="center", no_wrap=True)
            table.add_column("St", width=status_width, no_wrap=True)
            if i < 3:
                table.add_column("|", width=1, style="dim")

        def phase_text(phase):
            if phase == "✓":
                return Text("✓", style="green bold")
            elif phase == "P1":
                return Text("1", style="yellow")
            elif phase == "P2":
                return Text("2", style="blue")
            elif phase == "P3":
                return Text("3", style="magenta")
            return Text("-", style="dim")

        with self._display_lock:
            items = sorted(self._display_rows.items())
            # Group into rows of 4
            for i in range(0, len(items), 4):
                row_data = []
                for j in range(4):
                    if i + j < len(items):
                        req_id, row = items[i + j]
                        query = row["context"].replace("\n", " ")
                        # Show END of query (more distinctive), adapt to column width
                        q_chars = query_width - 2  # room for ".."
                        q_text = ".." + query[-q_chars:] if len(query) > query_width else query
                        # Compact status
                        status = row["status"][:status_width]
                        row_data.extend([req_id, q_text, phase_text(row["phase"]), status])
                    else:
                        row_data.extend(["", "", "", ""])
                    if j < 3:
                        row_data.append("|")
                table.add_row(*row_data)

        stats = self._display_stats
        footer = f"{stats['complete']}/{stats['total']} | {stats['tokens']:,}tok | ${stats['cost']:.4f}"
        table.caption = footer
        return table

    # =========================================================================
    # Phase 1: Planning (LWT Skeleton + Message)
    # =========================================================================

    def phase1_plan(self, query: str, items: List[dict], k: int = 1) -> Tuple[str, str]:
        """Phase 1: Generate evaluation STRATEGY (not execution).

        Strategy-centric design: Phase 1 sees schema but does NOT scan items.
        It outputs a strategy describing what conditions to check.

        Args:
            query: User request text (e.g., "Looking for a cafe...")
            items: List of item dicts (used for schema only)
            k: Number of top predictions

        Returns:
            Tuple of (strategy, message) for Phase 2
        """
        self._debug(1, "P1", f"Planning for: {query[:60]}...")

        n_items = len(items)

        # Show schema (1-2 example items) so LLM knows available fields
        # But don't ask LLM to scan all items
        filtered_items = filter_items_for_ranking(items)
        schema_compact = format_schema_compact(filtered_items[:2], num_examples=2, truncate=50)
        self._debug(2, "P1", f"Schema:\n{schema_compact[:500]}...")

        task_desc = RANKING_TASK_COMPACT.format(query=query, k=k)
        prompt = PHASE1_PROMPT.format(
            task_description=task_desc,
            schema_compact=schema_compact,
            n_items=n_items
        )

        response = call_llm(
            prompt,
            system=SYSTEM_PROMPT,
            role="planner",
            context={"method": "anot", "phase": 1, "step": "plan"}
        )

        self._log_llm_call("P1", "plan", prompt, response)
        self._debug(3, "P1", "Plan response:", response)

        # Parse response - now looking for ===STRATEGY=== instead of ===LWT_SKELETON===
        strategy = ""
        message = ""

        if "===STRATEGY===" in response:
            strat_start = response.index("===STRATEGY===") + len("===STRATEGY===")
            strat_end = response.find("===MESSAGE===", strat_start) if "===MESSAGE===" in response else len(response)
            strategy = response[strat_start:strat_end].strip()

        if "===MESSAGE===" in response:
            msg_start = response.index("===MESSAGE===") + len("===MESSAGE===")
            message = response[msg_start:].strip()

        self._debug(1, "P1", f"Strategy extracted: {len(strategy)} chars")
        return strategy, message

    # =========================================================================
    # Phase 2: ReAct LWT Expansion
    # =========================================================================

    def phase2_expand(self, strategy: str, message: str, n_items: int, query: dict) -> List[str]:
        """Phase 2: Generate batched LWT from strategy using ReAct loop.

        Args:
            strategy: Evaluation strategy from Phase 1 (conditions + logic)
            message: Additional notes from Phase 1
            n_items: Total number of items to evaluate
            query: Full query dict (for read() tool if needed)

        Returns:
            List of LWT steps
        """
        self._debug(1, "P2", f"ReAct expansion from strategy ({len(strategy)} chars)...")
        req_id = getattr(self._thread_local, 'request_id', None)
        if req_id:
            self._update_display(req_id, "P2", "ReAct expand")

        # Start with EMPTY LWT - Phase 2 generates it from strategy
        lwt_steps = []

        # Combine strategy and message for prompt
        full_strategy = strategy
        if message:
            full_strategy += f"\n\nNotes: {message}"

        prompt = PHASE2_PROMPT.format(strategy=full_strategy, n_items=n_items)
        conversation = [prompt]

        max_iterations = 50
        iteration = 0
        for iteration in range(max_iterations):
            self._debug(2, "P2", f"ReAct iteration {iteration + 1}")
            full_prompt = "\n".join(conversation)

            response = call_llm(
                full_prompt,
                system=SYSTEM_PROMPT,
                role="planner",
                context={"method": "anot", "phase": 2, "step": f"react_{iteration}"}
            )
            self._log_llm_call("P2", f"react_{iteration}", full_prompt, response)

            if not response.strip():
                self._debug(1, "P2", "Empty response, breaking")
                break

            # Process ALL tool calls in this response before checking done()
            action_results = []

            # Check for lwt_list()
            if "lwt_list()" in response:
                action_results.append(("lwt_list()", tool_lwt_list(lwt_steps)))

            # Process ALL lwt_insert() calls (common when LLM outputs multiple steps at once)
            for match in re.finditer(r'lwt_insert\((\d+),\s*"((?:[^"\\]|\\.)*)"\)', response, re.DOTALL):
                step = match.group(2).replace('\\"', '"').replace('\\n', '\n')
                result = tool_lwt_insert(int(match.group(1)), step, lwt_steps)
                action_results.append((f"lwt_insert({match.group(1)})", result))

            # Process ALL lwt_set() calls
            for match in re.finditer(r'lwt_set\((\d+),\s*"((?:[^"\\]|\\.)*)"\)', response, re.DOTALL):
                step = match.group(2).replace('\\"', '"').replace('\\n', '\n')
                result = tool_lwt_set(int(match.group(1)), step, lwt_steps)
                action_results.append((f"lwt_set({match.group(1)})", result))

            # Process ALL lwt_delete() calls
            for match in re.finditer(r'lwt_delete\((\d+)\)', response):
                result = tool_lwt_delete(int(match.group(1)), lwt_steps)
                action_results.append((f"lwt_delete({match.group(1)})", result))

            # Process ALL lwt_get() calls
            for match in re.finditer(r'lwt_get\((\d+)\)', response):
                result = tool_lwt_get(int(match.group(1)), lwt_steps)
                action_results.append((f"lwt_get({match.group(1)})", result))

            # Process ALL read() calls
            for match in re.finditer(r'read\("([^"]+)"\)', response):
                result = tool_read(match.group(1), query)
                if len(result) > 2000:
                    result = result[:2000] + "... (truncated)"
                action_results.append((f"read(\"{match.group(1)}\")", result))

            # Now check for done() - AFTER processing all other actions
            if "done()" in response.lower():
                self._debug(1, "P2", f"ReAct done after {iteration + 1} iterations, processed {len(action_results)} actions")
                break

            if action_results:
                # Combine all results into conversation
                results_text = "\n".join([f"{name}: {result}" for name, result in action_results])
                conversation.append(f"\n{response}\n\nRESULTS:\n{results_text}\n\nContinue:")
            else:
                self._debug(1, "P2", "No action found, prompting for action")
                conversation.append(f"\n{response}\n\nNo valid action found. Use lwt_list(), lwt_get(idx), lwt_set(idx, step), lwt_delete(idx), lwt_insert(idx, step), read(path), or done():")

        self._debug(1, "P2", f"Expanded LWT: {len(lwt_steps)} steps after {iteration + 1} iterations")

        trace = self._get_trace()
        if trace:
            trace["phase2"]["expanded_lwt"] = lwt_steps
            trace["phase2"]["react_iterations"] = iteration + 1

        return lwt_steps

    # =========================================================================
    # Phase 3: Pure LWT Execution
    # =========================================================================

    async def _execute_step_async(self, idx: str, instr: str, items: dict, user_query: str) -> Tuple[str, str]:
        """Execute a single LWT step asynchronously."""
        filled = substitute_variables(instr, items, user_query, self._get_cache())
        self._debug(3, "P3", f"Step {idx} filled:", filled)

        start = time.time()
        prompt_tokens = 0
        completion_tokens = 0
        try:
            result = await call_llm_async(
                filled,
                system=SYSTEM_PROMPT,
                role="worker",
                context={"method": "anot", "phase": 3, "step": idx},
                return_usage=True
            )
            output = result["text"]
            prompt_tokens = result["prompt_tokens"]
            completion_tokens = result["completion_tokens"]
        except Exception as e:
            output = "NO"
            error_msg = f"{type(e).__name__}: {str(e)}"
            req_id = getattr(self._thread_local, 'request_id', 'R??')
            self._errors.append((req_id, idx, error_msg))
            self._debug(1, "P3", f"ERROR in step {idx}: {e}", content=traceback.format_exc())

        latency = (time.time() - start) * 1000
        self._log_llm_call("P3", f"step_{idx}", filled, output)
        self._debug(2, "P3", f"Step {idx}: {output[:50]}... ({latency:.0f}ms)")

        step_data = {
            "output": output[:100] if len(output) > 100 else output,
            "latency_ms": latency,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
        if output == "NO" and 'error_msg' in locals():
            step_data["error"] = error_msg
        self._update_trace_step(idx, step_data)

        return idx, output

    async def _execute_parallel(self, lwt: str, items: dict, user_query: str) -> str:
        """Execute LWT with DAG parallel execution."""
        self._set_cache({})
        steps = parse_script(lwt)

        if not steps:
            self._debug(1, "P3", "ERROR: No valid steps in LWT")
            return ""

        layers = build_execution_layers(steps)
        self._debug(1, "P3", f"Executing {len(steps)} steps in {len(layers)} layers...")

        final = ""
        for layer in layers:
            tasks = [self._execute_step_async(idx, instr, items, user_query) for idx, instr in layer]
            results = await asyncio.gather(*tasks)
            for idx, output in results:
                self._cache_set(idx, output)
                final = output

        return final

    def phase3_execute(self, lwt: str, items: dict, user_query: str) -> str:
        """Execute the LWT script.

        Args:
            lwt: The LWT script to execute
            items: Restaurant data dict (for {(items)} substitution)
            user_query: User's request text (for {(query)} substitution)
        """
        req_id = getattr(self._thread_local, 'request_id', None)
        if req_id:
            self._update_display(req_id, "P3", "executing")

        try:
            return asyncio.run(self._execute_parallel(lwt, items, user_query))
        except RuntimeError:
            # Already in async context, run sequentially
            self._set_cache({})
            steps = parse_script(lwt)
            if not steps:
                return ""

            final = ""
            for idx, instr in steps:
                filled = substitute_variables(instr, items, user_query, self._get_cache())
                output = call_llm(
                    filled,
                    system=SYSTEM_PROMPT,
                    role="worker",
                    context={"method": "anot", "phase": 3, "step": idx}
                )
                self._log_llm_call("P3", f"step_{idx}", filled, output)
                self._cache_set(idx, output)
                final = output
            return final

    # =========================================================================
    # Main Entry Points
    # =========================================================================

    def evaluate(self, query, context: str) -> int:
        """Single item evaluation (not used for ranking)."""
        return 0

    def evaluate_ranking(self, query, context, k: int = 1, request_id: str = "R01") -> str:
        """Ranking evaluation: Phase 1 → Phase 2 → Phase 3.

        Args:
            query: User request text (e.g., "Looking for a cafe...")
            context: Restaurant data dict {"items": {...}} or JSON string
            k: Number of top predictions
            request_id: Request identifier for tracing
        """
        self._init_trace(request_id, query)
        self._thread_local.request_id = request_id

        # Parse restaurant data from context (not query!)
        if isinstance(context, str):
            data = json.loads(context)
        else:
            data = context

        # Extract items - handle both list and dict formats
        raw_items = data.get('items', [data]) if isinstance(data, dict) else [data]
        if isinstance(raw_items, dict):
            # Dict format: {"1": item1, "2": item2, ...} - convert to list ordered by key
            items = [raw_items[k] for k in sorted(raw_items.keys(), key=lambda x: int(x))]
        else:
            items = raw_items
        n_items = len(items)

        self._debug(1, "INIT", f"Ranking {n_items} items for: {query[:60]}...")
        self._update_display(request_id, "---", "starting", query)
        trace = self._get_trace()

        # Phase 1: Strategy extraction (schema-aware, no item scanning)
        self._update_display(request_id, "P1", "planning")
        p1_start = time.time()
        strategy, message = self.phase1_plan(query, items, k)
        p1_latency = (time.time() - p1_start) * 1000

        if trace:
            trace["phase1"]["strategy"] = strategy[:500] if strategy else ""
            trace["phase1"]["message"] = message[:500] if message else ""
            trace["phase1"]["latency_ms"] = p1_latency
            self._save_trace_incremental(request_id)

        # Phase 2: Generate batched LWT from strategy
        self._update_display(request_id, "P2", "expanding")
        p2_start = time.time()
        expanded_lwt_steps = self.phase2_expand(strategy, message, n_items, data)
        p2_latency = (time.time() - p2_start) * 1000
        expanded_lwt = "\n".join(expanded_lwt_steps)

        if trace:
            trace["phase2"]["latency_ms"] = p2_latency
            self._save_trace_incremental(request_id)

        # Phase 3: Execute with items data and user query text
        self._update_display(request_id, "P3", "executing")
        p3_start = time.time()
        output = self.phase3_execute(expanded_lwt, data, query)
        p3_latency = (time.time() - p3_start) * 1000

        # Parse final output (LLM outputs 1-indexed)
        indices = []
        for match in re.finditer(r'\b(\d+)\b', output):
            idx = int(match.group(1))
            if 1 <= idx <= n_items and idx not in indices:
                indices.append(idx)

        if not indices:
            indices = list(range(1, min(k, n_items) + 1))  # 1-indexed fallback

        top_k = [str(idx) for idx in indices[:k]]  # Already 1-indexed
        self._debug(1, "P3", f"Final ranking: {','.join(top_k)}")

        if trace:
            trace["phase3"]["top_k"] = [int(x) for x in top_k]
            trace["phase3"]["final_output"] = output[:500]
            trace["phase3"]["latency_ms"] = p3_latency
            self._save_trace_incremental(request_id)

        self._update_display(request_id, "✓", ",".join(top_k))
        self._thread_local.request_id = None

        return ", ".join(top_k)


def create_method(run_dir: str = None, defense: bool = False, debug: bool = False):
    """Factory function to create ANoT instance."""
    return AdaptiveNetworkOfThought(run_dir=run_dir, defense=defense, verbose=debug)
