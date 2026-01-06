#!/usr/bin/env python3
"""ReACT (Reasoning and Acting) method for restaurant recommendation.

Reference: ReAct: Synergizing Reasoning and Acting in Language Models
Yao et al., ICLR 2023
https://arxiv.org/abs/2210.03629

Redesigned to use dict mode with path-based data access (like ANoT).
"""

import json
import re
from typing import Tuple, List

from .base import BaseMethod
from .anot.tools import tool_read
from utils.llm import call_llm
from utils.parsing import parse_final_answer


MAX_STEPS = 8

SYSTEM_PROMPT = """You are evaluating restaurants to find the best match for a user's request.
Use the ReACT format: Thought, Action, Observation loop.

Available actions:
- read(path): Read data at path. Examples:
  - read("items.1.name") → restaurant name
  - read("items.1.reviews") → all reviews for restaurant 1
  - read("items.1.reviews.0.text") → first review text
  - read("items.1.attributes") → restaurant attributes
  - read("items.1.categories") → restaurant categories
- count(path): Count items at path. Example: count("items") → number of restaurants
- schema(): Show data structure with example paths
- finish(answer): Submit final answer (comma-separated indices, e.g., "3, 1, 5")

Path format: Use dot notation. Items are 1-indexed (items.1, items.2, ...).

You MUST respond in this exact format:
Thought: [your reasoning about what to do next]
Action: [action with arguments]

Example:
Thought: I need to see how many restaurants there are.
Action: count("items")"""

SYSTEM_PROMPT_RANKING = """You are selecting the best restaurants for a user's request.
You have access to structured restaurant data via path-based queries.

Available actions:
- read(path): Read data at path
  - read("items.1.name") → restaurant 1's name
  - read("items.1.reviews") → all reviews
  - read("items.1.reviews.0.text") → first review text
  - read("items.1.attributes.NoiseLevel") → noise level
  - read("items.1.hours") → operating hours
- count(path): Count items (e.g., count("items"), count("items.1.reviews"))
- schema(): Show data structure
- finish(answer): Submit final ranking as comma-separated indices (best first)

Items are 1-indexed. Use systematic exploration to find the best matches.

Format your response as:
Thought: [reasoning]
Action: [action call]"""


def _extract_schema(data: dict, max_depth: int = 3) -> str:
    """Extract schema from data dict showing available paths."""
    lines = []

    def traverse(obj, path="", depth=0):
        if depth > max_depth:
            return
        if isinstance(obj, dict):
            for k, v in list(obj.items())[:5]:  # Limit keys shown
                new_path = f"{path}.{k}" if path else k
                if isinstance(v, dict):
                    lines.append(f"  {new_path}.* (dict with {len(v)} keys)")
                    if depth < max_depth - 1:
                        traverse(v, new_path, depth + 1)
                elif isinstance(v, list):
                    lines.append(f"  {new_path}[0..{len(v)-1}] (list of {len(v)})")
                    if v and depth < max_depth - 1:
                        traverse(v[0], f"{new_path}.0", depth + 1)
                else:
                    val_preview = str(v)[:50] + "..." if len(str(v)) > 50 else str(v)
                    lines.append(f"  {new_path} = {val_preview}")
        elif isinstance(obj, list) and obj:
            traverse(obj[0], f"{path}.0", depth + 1)

    traverse(data)
    return "Data schema:\n" + "\n".join(lines[:30])  # Limit output


def _count_at_path(path: str, data: dict) -> str:
    """Count items at a path."""
    result = tool_read(path, data)
    if result.startswith("Error:"):
        return result
    try:
        parsed = json.loads(result) if result.startswith(("[", "{")) else result
        if isinstance(parsed, (list, dict)):
            return str(len(parsed))
        return "1"
    except (json.JSONDecodeError, TypeError):
        return "1"


class ReAct(BaseMethod):
    """ReACT (Reasoning and Acting) with dict-mode data access."""

    name = "react"

    def __init__(self, run_dir: str = None, **kwargs):
        super().__init__(run_dir=run_dir, **kwargs)

    def evaluate(self, query: str, context: str) -> int:
        """Single item evaluation (not primary use case)."""
        return 0

    def _build_ranking_prompt(self, query: str, n_items: int, history: List[dict], k: int = 1) -> str:
        """Build prompt for ranking task."""
        if k == 1:
            instruction = "Select the restaurant that BEST matches the user's request."
        else:
            instruction = f"Select the TOP {k} restaurants that best match the user's request."

        parts = []
        parts.append(f"[USER REQUEST]")
        parts.append(query)
        parts.append("")
        parts.append(f"[DATA INFO]")
        parts.append(f"There are {n_items} restaurants (items.1 through items.{n_items}).")
        parts.append("Use read(path) to explore restaurant data, then finish(answer) with your ranking.")
        parts.append("")
        parts.append(f"[INSTRUCTION]")
        parts.append(instruction)
        parts.append("")

        if history:
            parts.append("[PREVIOUS STEPS]")
            for i, step in enumerate(history, 1):
                parts.append(f"Step {i}:")
                parts.append(f"Thought: {step['thought']}")
                parts.append(f"Action: {step['action']}")
                parts.append(f"Observation: {step['observation']}")
                parts.append("")

        parts.append("[YOUR TURN]")
        parts.append("Thought: ")

        return "\n".join(parts)

    def _parse_response(self, response: str) -> Tuple[str, str]:
        """Parse Thought and Action from response."""
        thought = ""
        action = ""

        # Extract Thought
        thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\Z)", response, re.DOTALL | re.IGNORECASE)
        if thought_match:
            thought = thought_match.group(1).strip()

        # Extract Action
        action_match = re.search(r"Action:\s*(.+?)(?=\nThought:|\nObservation:|\Z)", response, re.DOTALL | re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip()

        return thought, action

    def _execute_action(self, action: str, data: dict) -> Tuple[str, bool, str]:
        """Execute an action and return (observation, is_finished, answer).

        Returns:
            Tuple of (observation, is_finished, final_answer)
        """
        action = action.strip()

        # Check for finish action
        finish_match = re.search(r'finish\s*\(\s*["\']?([^"\')\]]+)["\']?\s*\)', action, re.IGNORECASE)
        if finish_match:
            answer = finish_match.group(1).strip()
            return f"Final answer submitted: {answer}", True, answer

        # Check for read action
        read_match = re.search(r'read\s*\(\s*["\']([^"\']+)["\']\s*\)', action, re.IGNORECASE)
        if read_match:
            path = read_match.group(1)
            result = tool_read(path, data)
            # Truncate very long results
            if len(result) > 3000:
                result = result[:3000] + "\n... (truncated, use more specific path)"
            return result, False, ""

        # Check for count action
        count_match = re.search(r'count\s*\(\s*["\']([^"\']+)["\']\s*\)', action, re.IGNORECASE)
        if count_match:
            path = count_match.group(1)
            result = _count_at_path(path, data)
            return result, False, ""

        # Check for schema action
        if re.search(r'schema\s*\(\s*\)', action, re.IGNORECASE):
            return _extract_schema(data), False, ""

        # Unknown action
        return (
            f"Unknown action: {action}. "
            "Use read(\"path\"), count(\"path\"), schema(), or finish(\"answer\").",
            False,
            ""
        )

    def _parse_indices(self, text: str, max_index: int = 20, k: int = 5) -> list:
        """Parse up to k indices from text."""
        if text is None:
            return []
        indices = []
        for match in re.finditer(r'\b(\d+)\b', str(text)):
            idx = int(match.group(1))
            if 1 <= idx <= max_index and idx not in indices:
                indices.append(idx)
                if len(indices) >= k:
                    break
        return indices

    def _format_indices(self, indices: list, k: int) -> str:
        """Format indices as comma-separated string."""
        if not indices:
            return "1"
        return ", ".join(str(i) for i in indices[:k])

    def evaluate_ranking(self, query: str, context, k: int = 1, **kwargs) -> str:
        """Evaluate ranking task using ReACT loop with dict-mode data access.

        Args:
            query: User request text
            context: Restaurant data dict {"items": {"1": {...}, ...}} or JSON string
            k: Number of top predictions

        Returns:
            Comma-separated indices (e.g., "3, 1, 5")
        """
        # Parse context
        if isinstance(context, str):
            data = json.loads(context)
        else:
            data = context

        # Get item count
        items = data.get("items", {})
        if isinstance(items, dict):
            n_items = len(items)
        else:
            n_items = len(items) if items else 0

        history = []

        for step in range(MAX_STEPS):
            prompt = self._build_ranking_prompt(query, n_items, history, k)
            response = call_llm(prompt, system=SYSTEM_PROMPT_RANKING)

            thought, action = self._parse_response(response)

            if not action:
                # No action found, prompt for one
                action = "schema()"

            observation, is_finished, answer = self._execute_action(action, data)

            if is_finished:
                indices = self._parse_indices(answer, max_index=n_items, k=k)
                if not indices:
                    # Try parsing from full response
                    indices = self._parse_indices(response, max_index=n_items, k=k)
                return self._format_indices(indices, k)

            history.append({
                "thought": thought,
                "action": action,
                "observation": observation
            })

        # Max steps reached - force decision
        prompt = self._build_ranking_prompt(query, n_items, history, k)
        prompt += f"\nYou have reached the maximum steps. You MUST now submit your answer."
        prompt += f"\nThought: Based on my exploration, I will select the best restaurants."
        prompt += f"\nAction: finish(\""

        response = call_llm(prompt, system=SYSTEM_PROMPT_RANKING)
        indices = self._parse_indices(response, max_index=n_items, k=k)
        return self._format_indices(indices, k)
