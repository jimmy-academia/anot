#!/usr/bin/env python3
"""ANoT - Adaptive Network of Thought.

Key innovation: Analyzes context to identify evidence types (metadata/hours/reviews)
and generates LWT scripts tailored to the specific evidence sources.
"""

import os
import json
import time
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme

from .shared import (
    DEBUG,
    SYSTEM_PROMPT,
    call_llm,
    substitute_variables,
    parse_script,
    parse_final_answer,
)

# =============================================================================
# Rich Console for Debug Output
# =============================================================================

ANOT_THEME = Theme({
    "phase": "bold magenta",
    "subphase": "bold cyan",
    "context": "yellow",
    "script": "green",
    "step": "bold blue",
    "output": "white",
    "time": "dim",
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
})
console = Console(theme=ANOT_THEME, force_terminal=True)


# =============================================================================
# Prompts
# =============================================================================

CONTEXT_ANALYSIS_PROMPT = """Analyze this user request to understand what they need.

Request: {context}

Identify:
1. What conditions must be satisfied? (list each one)
2. For each condition, where would you find evidence?
   - METADATA: attributes like WiFi, NoiseLevel, OutdoorSeating, Alcohol, RestaurantsPriceRange2, DogsAllowed, BikeParking, Ambience, HasTV
   - HOURS: time-based constraints (open on specific day, available during specific hours)
   - REVIEWS: subjective qualities mentioned in customer reviews (good matcha, aesthetic, cozy, latte art, books)

Output format:
CONDITIONS:
- [condition 1]: [METADATA/HOURS/REVIEWS] - [what to check]
- [condition 2]: [METADATA/HOURS/REVIEWS] - [what to check]
...

LOGIC: AND (all must be satisfied)
"""

SCRIPT_GENERATION_PROMPT = """Generate an LWT script to evaluate this restaurant.

USER REQUEST ANALYSIS:
{context_analysis}

AVAILABLE DATA:
- Attributes: {attribute_keys}
- Hours: {available_days}
- Reviews: {review_count} reviews (avg {avg_review_length:.0f} chars)

RESTAURANT DATA STRUCTURE:
{{(input)}}[attributes][<key>] - for metadata (values are strings like "'free'", "u'quiet'", "True", "False")
{{(input)}}[hours][<Day>] - for hours (format: "7:0-19:0" means 7am-7pm)
{{(input)}}[item_data][<i>][review] - for review text (i is 0-indexed)

Generate an LWT script with these rules:
1. Each line: (N)=LLM("instruction")
2. Use {{(input)}} for restaurant data, {{(context)}} for user request
3. Use {{(N)}} to reference previous step results
4. For METADATA conditions: check {{(input)}}[attributes][<key>] directly
5. For HOURS conditions: check {{(input)}}[hours][<Day>] and parse time ranges
6. For REVIEWS conditions: analyze {{(input)}}[item_data][i][review] for EACH review, then aggregate
7. Final step must combine all results and output exactly: -1, 0, or 1

Example for "quiet cafe with WiFi open Monday 10am":
(0)=LLM("Value is {{(input)}}[attributes][NoiseLevel]. Is it quiet? Output: 1 if quiet/average, -1 if loud, 0 if missing")
(1)=LLM("Value is {{(input)}}[attributes][WiFi]. Is it free? Output: 1 if free, 0 if paid/unclear, -1 if none")
(2)=LLM("Hours are {{(input)}}[hours][Monday]. Is 10:00 within these hours? Output: 1 if yes, -1 if no/closed, 0 if unclear")
(3)=LLM("Combine: noise={{(0)}}, wifi={{(1)}}, hours={{(2)}}. If any -1: output -1. If all 1: output 1. Else: 0")

Example for "cafe with good matcha in reviews" (3 reviews):
(0)=LLM("Review: {{(input)}}[item_data][0][review]. Mentions good matcha? Output: POSITIVE, NEGATIVE, or NONE")
(1)=LLM("Review: {{(input)}}[item_data][1][review]. Mentions good matcha? Output: POSITIVE, NEGATIVE, or NONE")
(2)=LLM("Review: {{(input)}}[item_data][2][review]. Mentions good matcha? Output: POSITIVE, NEGATIVE, or NONE")
(3)=LLM("Aggregate {{(0)}}, {{(1)}}, {{(2)}}: Count POSITIVE vs NEGATIVE. More positive=1, more negative=-1, mixed/none=0")

Example for "outdoor seating + aesthetic in reviews" (2 reviews):
(0)=LLM("Value is {{(input)}}[attributes][OutdoorSeating]. Is it True? Output: 1 if True, -1 if False, 0 if missing")
(1)=LLM("Review: {{(input)}}[item_data][0][review]. Describes aesthetic/instagram-worthy? POSITIVE/NEGATIVE/NONE")
(2)=LLM("Review: {{(input)}}[item_data][1][review]. Describes aesthetic/instagram-worthy? POSITIVE/NEGATIVE/NONE")
(3)=LLM("Aggregate {{(1)}}, {{(2)}}: More POSITIVE=1, more NEGATIVE=-1, else=0")
(4)=LLM("Combine: outdoor={{(0)}}, aesthetic={{(3)}}. If any -1: output -1. If all 1: output 1. Else: 0")

Now generate the script for this request. Output ONLY the script lines, nothing else:
"""


# =============================================================================
# ANoT Implementation
# =============================================================================

class AdaptiveNetworkOfThought:
    """Adaptive Network of Thought - context-aware LWT script generation."""

    def __init__(self, run_dir: str = None, debug: bool = False):
        self.run_dir = run_dir
        self.debug = debug or DEBUG
        self.cache = {}

    def phase1_analyze_context(self, context: str) -> str:
        """Phase 1: Analyze context to identify conditions and evidence sources."""
        prompt = CONTEXT_ANALYSIS_PROMPT.format(context=context)

        if self.debug:
            console.print(Panel("PHASE 1: Context Analysis", style="phase"))
            console.print("[dim]Prompt:[/dim]")
            console.print(prompt, style="dim")

        start = time.time()
        analysis = call_llm(prompt, system=SYSTEM_PROMPT, role="planner")
        duration = time.time() - start

        if self.debug:
            console.print(f"\n[time]Duration: {duration:.2f}s[/time]")
            console.print("[subphase]Analysis Result:[/subphase]")
            console.print(analysis)
            console.rule()

        return analysis

    def phase1b_analyze_query(self, query: dict) -> dict:
        """Phase 1b: Analyze query structure (deterministic, no LLM)."""
        attributes = query.get("attributes", {})
        hours = query.get("hours", {})
        reviews = query.get("item_data", [])

        # Calculate review stats
        review_lengths = [len(r.get("review", "")) for r in reviews]
        avg_length = sum(review_lengths) / max(len(review_lengths), 1)

        info = {
            "attribute_keys": list(attributes.keys()),
            "has_hours": bool(hours),
            "available_days": list(hours.keys()) if hours else [],
            "review_count": len(reviews),
            "avg_review_length": avg_length,
        }

        if self.debug:
            console.print(Panel("PHASE 1b: Query Structure", style="phase"))
            table = Table(show_header=True)
            table.add_column("Type", style="cyan")
            table.add_column("Available Data", style="white")
            table.add_row("Attributes", ", ".join(info['attribute_keys']) or "(none)")
            table.add_row("Hours", ", ".join(info['available_days']) or "(none)")
            table.add_row("Reviews", f"{info['review_count']} reviews (avg {info['avg_review_length']:.0f} chars)")
            console.print(table)
            console.rule()

        return info

    def phase2_generate_script(self, context_analysis: str, query_info: dict,
                                query: dict, context: str) -> str:
        """Phase 2: Generate LWT script tailored to evidence types."""
        prompt = SCRIPT_GENERATION_PROMPT.format(
            context_analysis=context_analysis,
            attribute_keys=", ".join(query_info["attribute_keys"]) or "(none)",
            available_days=", ".join(query_info["available_days"]) or "(none)",
            review_count=query_info["review_count"],
            avg_review_length=query_info["avg_review_length"],
        )

        if self.debug:
            console.print(Panel("PHASE 2: Script Generation", style="phase"))

        start = time.time()
        script = call_llm(prompt, system=SYSTEM_PROMPT, role="planner")
        duration = time.time() - start

        if self.debug:
            console.print(f"[time]Duration: {duration:.2f}s[/time]")
            console.print("[subphase]Generated Script:[/subphase]")
            console.print(Syntax(script, "python", theme="monokai", line_numbers=True))
            console.rule()

        return script

    def _execute_step_sync(self, idx: str, instr: str, query: dict, context: str) -> str:
        """Execute a single step synchronously."""
        filled = substitute_variables(instr, query, context, self.cache)

        if self.debug:
            console.print(f"\n[step]Step ({idx})[/step]")
            console.print(f"  [dim]Instruction:[/dim] {instr}")
            console.print(f"  [dim]Filled:[/dim] {filled[:300]}{'...' if len(filled) > 300 else ''}")

        try:
            start = time.time()
            output = call_llm(filled, system=SYSTEM_PROMPT, role="worker")
            duration = time.time() - start
        except Exception as e:
            output = "0"
            duration = 0
            if self.debug:
                console.print(f"  [error]Error: {e}[/error]")

        if self.debug:
            console.print(f"  [output]→ {output}[/output] [time]({duration:.2f}s)[/time]")

        return output

    def execute_script(self, script: str, query: dict, context: str) -> str:
        """Phase 3: Execute LWT script step by step."""
        self.cache = {}
        steps = parse_script(script)

        if not steps:
            # Fallback to direct LLM call
            if self.debug:
                console.print("[warning]No steps parsed, using fallback[/warning]")
            return self._fallback_direct(query, context)

        if self.debug:
            console.print(Panel(f"PHASE 3: Execution ({len(steps)} steps)", style="phase"))

        final = ""
        for idx, instr in steps:
            output = self._execute_step_sync(idx, instr, query, context)
            self.cache[idx] = output
            final = output

        if self.debug:
            console.rule()

        return final

    def _fallback_direct(self, query: dict, context: str) -> str:
        """Fallback when script parsing fails."""
        prompt = f"""Based on restaurant data:
{json.dumps(query, indent=2)[:2000]}

User wants: {context}

Should this restaurant be recommended?
Output ONLY: -1 (no), 0 (unclear), or 1 (yes)"""

        return call_llm(prompt, system=SYSTEM_PROMPT, role="worker")

    def solve(self, query, context: str) -> int:
        """Full pipeline: analyze → generate script → execute."""
        if self.debug:
            console.print()
            console.print(Panel.fit("[bold white]ANoT SOLVE[/bold white]", style="on blue"))
            console.print(f"[context]Context:[/context] {context}")
            console.print(f"[context]Item:[/context] {query.get('item_name', 'Unknown')}")
            console.rule()

        # Phase 1: Analyze context (what to check)
        context_analysis = self.phase1_analyze_context(context)

        # Phase 1b: Analyze query structure (what data is available)
        query_info = self.phase1b_analyze_query(query)

        # Phase 2: Generate LWT script
        script = self.phase2_generate_script(context_analysis, query_info, query, context)

        # Phase 3: Execute script
        output = self.execute_script(script, query, context)

        # Parse final answer
        answer = parse_final_answer(output)

        if self.debug:
            if answer == 1:
                console.print(Panel(f"[success]Final Answer: {answer} (RECOMMEND)[/success]", style="green"))
            elif answer == -1:
                console.print(Panel(f"[error]Final Answer: {answer} (NOT RECOMMEND)[/error]", style="red"))
            else:
                console.print(Panel(f"[warning]Final Answer: {answer} (UNCLEAR)[/warning]", style="yellow"))
            console.print()

        return answer


# =============================================================================
# Factory and Method Interface
# =============================================================================

_executor = None


def create_method(run_dir: str = None, debug: bool = False):
    """Factory function to create ANoT method."""
    def method_fn(query, context: str) -> int:
        global _executor
        if _executor is None:
            _executor = AdaptiveNetworkOfThought(run_dir=run_dir, debug=debug)
        try:
            return _executor.solve(query, context)
        except Exception as e:
            if debug or DEBUG:
                console.print(f"[error]Error: {e}[/error]")
            return 0
    return method_fn


def method(query, context: str) -> int:
    """Default ANoT method."""
    return create_method()(query, context)
