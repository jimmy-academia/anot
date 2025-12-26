#!/usr/bin/env python3
"""Knowledge Network of Thought - dynamic script generation with dual-mode input."""

import os
import re
import json
import ast
from llm import call_llm

DEBUG = os.environ.get("KNOT_DEBUG", "0") == "1"

# Task-specific prompts for restaurant recommendation
TASK_CONCEPT = """You are evaluating whether a restaurant should be recommended to a user.
The input contains restaurant info: item_name, city, neighborhood, price_range, cuisine, and item_data (list of reviews).
Each review in item_data has: review_id and review text.
The context describes what the user is looking for.
Output a final recommendation: 1 (recommend), 0 (neutral/uncertain), -1 (not recommend).
Break down the analysis: extract requirements, analyze reviews, check evidence, synthesize."""

TASK_EXAMPLE_STRING = """example for restaurant recommendation (string mode)
(0)=LLM("Extract 3-5 key requirements from the user request: {(context)}")
(1)=LLM("Split the reviews from the restaurant info into a list: {(input)}")
(2)=LLM("For each review in {(1)}, summarize key points about atmosphere, service, price, food quality")
(3)=LLM("For each requirement in {(0)}, check if {(2)} provides POSITIVE, NEGATIVE, or NO CLEAR evidence")
(4)=LLM("Count evidence from {(3)}: how many POSITIVE vs NEGATIVE? If POSITIVE > NEGATIVE output 1. If NEGATIVE > POSITIVE output -1. Otherwise output 0. Output ONLY the number.")"""

TASK_EXAMPLE_DICT = """example for restaurant recommendation (dict mode)
(0)=LLM("Extract 3-5 key requirements from: {(context)}")
(1)=LLM("Restaurant is {(input)}[item_name] in {(input)}[neighborhood], price {(input)}[price_range]. Summarize this context.")
(2)=LLM("Summarize this review for key points: {(input)}[item_data][0][review]")
(3)=LLM("Summarize this review for key points: {(input)}[item_data][1][review]")
(4)=LLM("Combine review summaries: {(2)}, {(3)}. List overall positive and negative points.")
(5)=LLM("Check requirements {(0)} against evidence {(4)}. For each requirement: POSITIVE, NEGATIVE, or UNCLEAR.")
(6)=LLM("Based on {(5)}: count POSITIVE vs NEGATIVE. If POSITIVE > NEGATIVE output 1. If NEGATIVE > POSITIVE output -1. Otherwise 0. Output ONLY the number.")"""

KNOWLEDGE_PROMPT = """Given this task:
%s

Please create a step-by-step solution approach.
Each step should be simple and focused on one sub-task.
Don't use loops - list each step explicitly.
Use Step0, Step1, Step2 to represent intermediate results.

Key steps should include:
1. Extract user requirements from context
2. Parse/summarize review information from input
3. Check each requirement against the evidence
4. Synthesize findings into a final recommendation (1, 0, or -1)
"""

SCRIPT_PROMPT = """Create an executable script for restaurant recommendation.
Each line: (N)=LLM("instruction")
Use {(input)} for restaurant data, {(context)} for user request.
Use {(N)} to reference previous results. Use [key] or [index] for access.

Example:
%s

Based on this approach:
%s

Create a script for:
%s

Requirements:
- Final step must output exactly: -1, 0, or 1
- Each step on its own line: (N)=LLM("...")
- No text after the script
"""

SYSTEM_PROMPT = "You follow instructions precisely. Output only what is requested."


def substitute_variables(instruction: str, query, context: str, cache: dict) -> str:
    """Substitute {(var)}[key][index] patterns with actual values."""
    pattern = r'\{\((\w+)\)\}((?:\[[^\]]+\])*)'

    def _sub(match):
        var = match.group(1)
        accessors = match.group(2) or ''

        # Get base value
        if var == 'input':
            val = query
        elif var == 'context':
            val = context
        else:
            val = cache.get(var, '')

        # Try to parse string as literal if needed
        if isinstance(val, str) and accessors:
            try:
                parsed = ast.literal_eval(val)
                if isinstance(parsed, (dict, list, tuple)):
                    val = parsed
            except:
                pass

        # Apply accessors [key] or [index]
        for acc in re.findall(r'\[([^\]]+)\]', accessors):
            try:
                if isinstance(val, dict):
                    val = val.get(acc, val.get(int(acc)) if acc.isdigit() else '')
                elif isinstance(val, (list, tuple)) and acc.isdigit():
                    idx = int(acc)
                    val = val[idx] if 0 <= idx < len(val) else ''
                else:
                    val = ''
            except:
                val = ''

        # Return as string
        if isinstance(val, (dict, list, tuple)):
            return json.dumps(val)
        return str(val)

    return re.sub(pattern, _sub, instruction)


def parse_script(script: str) -> list:
    """Parse script into [(index, instruction), ...]."""
    steps = []
    for line in script.split('\n'):
        if '=LLM(' not in line:
            continue
        idx_match = re.search(r'\((\d+)\)\s*=\s*LLM', line)
        instr_match = re.search(r'LLM\(["\'](.+?)["\']\)', line, re.DOTALL)
        if idx_match and instr_match:
            steps.append((idx_match.group(1), instr_match.group(1)))
    return steps


def parse_final_answer(output: str) -> int:
    """Parse output to -1, 0, or 1."""
    output = output.strip()
    if output in ["-1", "0", "1"]:
        return int(output)

    match = re.search(r'(?:^|[:\s])(-1|0|1)(?:\s|$|\.)', output)
    if match:
        return int(match.group(1))

    lower = output.lower()
    if "not recommend" in lower:
        return -1
    if "recommend" in lower and "not" not in lower:
        return 1
    return 0


class KnowledgeNetworkOfThought:
    """Dynamic 2-phase script generation: knowledge → script → execute."""

    def __init__(self, mode="string"):
        self.mode = mode
        self.cache = {}

    def generate_knowledge(self, query, context: str) -> str:
        """Phase 1: Generate step-by-step approach."""
        if self.mode == "dict":
            goal = f"Input (dict): {json.dumps(query)}\nContext: {context}"
        else:
            goal = f"Input: {query}\nContext: {context}"

        prompt = KNOWLEDGE_PROMPT % goal
        knowledge = call_llm(prompt, system=SYSTEM_PROMPT)

        if DEBUG:
            print("=" * 50)
            print("KNOWLEDGE:")
            print(knowledge)
            print("=" * 50)

        return knowledge

    def generate_script(self, knowledge: str, query, context: str) -> str:
        """Phase 2: Generate executable script from knowledge."""
        if self.mode == "dict":
            goal = f"Input (dict with keys: item_name, city, neighborhood, price_range, cuisine, item_data): {json.dumps(query)[:500]}...\nContext: {context}"
            example = TASK_EXAMPLE_DICT
        else:
            goal = f"Input: {str(query)[:500]}...\nContext: {context}"
            example = TASK_EXAMPLE_STRING

        prompt = SCRIPT_PROMPT % (example, knowledge, goal)
        script = call_llm(prompt, system=SYSTEM_PROMPT)

        if DEBUG:
            print("SCRIPT:")
            print(script)
            print("=" * 50)

        return script

    def execute_script(self, script: str, query, context: str) -> str:
        """Execute script step by step."""
        self.cache = {}
        steps = parse_script(script)

        if not steps:
            # Fallback: direct answer
            fallback = f"Based on restaurant: {query}\nUser wants: {context}\nRecommend? Output only: -1, 0, or 1"
            return call_llm(fallback, system=SYSTEM_PROMPT)

        final = ""
        for idx, instr in steps:
            filled = substitute_variables(instr, query, context, self.cache)

            if DEBUG:
                print(f"Step ({idx}): {filled[:100]}...")

            try:
                output = call_llm(filled, system=SYSTEM_PROMPT)
            except Exception as e:
                output = "0"
                if DEBUG:
                    print(f"  Error: {e}")

            # Cache result
            try:
                self.cache[idx] = ast.literal_eval(output)
            except:
                self.cache[idx] = output

            final = output
            if DEBUG:
                print(f"  -> {output[:100]}...")

        return final

    def solve(self, query, context: str) -> int:
        """Full pipeline: knowledge → script → execute → parse."""
        knowledge = self.generate_knowledge(query, context)
        script = self.generate_script(knowledge, query, context)
        output = self.execute_script(script, query, context)
        return parse_final_answer(output)


_executor = None
_current_mode = None


def create_method(mode="string"):
    """Factory to create method with specific mode."""
    def method(query, context: str) -> int:
        global _executor, _current_mode
        if _executor is None or _current_mode != mode:
            _executor = KnowledgeNetworkOfThought(mode=mode)
            _current_mode = mode
        try:
            return _executor.solve(query, context)
        except Exception as e:
            if DEBUG:
                print(f"Error: {e}")
            return 0
    return method


# Default method (string mode)
def method(query, context: str) -> int:
    """Default KNoT method using string mode."""
    return create_method("string")(query, context)
