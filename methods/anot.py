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

CONTEXT_ANALYSIS_PROMPT = """What conditions must a restaurant satisfy for this request?

Request: "{context}"

List each condition and where to find evidence:
- METADATA: WiFi, NoiseLevel, OutdoorSeating, Alcohol, RestaurantsPriceRange2, DogsAllowed, BikeParking, HasTV
- HOURS: open on specific day/time
- REVIEWS: subjective qualities (matcha, aesthetic, cozy, books)

Example output for "quiet cafe with free Wi-Fi and no TV":
CONDITIONS:
- quiet: METADATA - NoiseLevel should be 'quiet' or 'low'
- free WiFi: METADATA - WiFi should be 'free'
- no TV: METADATA - HasTV should be False

Now list conditions for the request above:
"""

SCRIPT_GENERATION_PROMPT = """Write a script to check: {context}

Conditions: {context_analysis}

CRITICAL FORMAT RULES:
1. Access attributes: {{(input)}}[attributes][WiFi], {{(input)}}[attributes][NoiseLevel], etc.
2. Access hours: {{(input)}}[hours][Monday], {{(input)}}[hours][Tuesday], etc.
3. Access reviews: {{(input)}}[item_data][0][review], {{(input)}}[item_data][1][review], etc.
4. Every instruction MUST end with: Output ONLY -1, 0, or 1
5. Reference previous: {{(0)}}, {{(1)}}, etc.

VALUE INTERPRETATION:
- NoiseLevel: 'quiet'=good, 'average'=bad, 'loud'=bad
- WiFi: 'free'=good, anything else=bad
- Boolean attributes: True=yes, False=no

Example:
(0)=LLM("{{(input)}}[attributes][NoiseLevel]. If 'quiet' output 1. If 'average' or 'loud' output -1. Output ONLY -1, 0, or 1")
(1)=LLM("{{(input)}}[attributes][WiFi]. If 'free' output 1. Else output -1. Output ONLY -1, 0, or 1")
(2)=LLM("{{(0)}}={{(0)}}, {{(1)}}={{(1)}}. If any -1 then output -1. If all 1 then output 1. Else output 0. Output ONLY -1, 0, or 1")

Script:
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
        # Fallback if context_analysis is empty
        if not context_analysis or not context_analysis.strip():
            context_analysis = f"(extract conditions from the user request)"

        prompt = SCRIPT_GENERATION_PROMPT.format(
            context=context,
            context_analysis=context_analysis,
            attribute_keys=", ".join(query_info["attribute_keys"]) or "(none)",
        )

        if self.debug:
            console.print(Panel("PHASE 2: Script Generation", style="phase"))
            console.print("[dim]Prompt being sent:[/dim]")
            console.print(f"[dim]{prompt[:1000]}...[/dim]")

        start = time.time()
        script = call_llm(prompt, system=SYSTEM_PROMPT, role="planner")
        duration = time.time() - start

        if self.debug:
            console.print(f"[time]Duration: {duration:.2f}s[/time]")
            console.print(f"[subphase]Generated Script (len={len(script)}):[/subphase]")
            console.print(f"[dim]>>>{repr(script)}<<<[/dim]")
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
