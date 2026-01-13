#!/usr/bin/env python3
"""Phase 2 tools for LWT manipulation and data access."""

import json
import re
from typing import List


def tool_read(path: str, data: dict) -> str:
    """Read full value at path."""
    def resolve_path(p: str, d):
        if not p:
            return d
        # Parse path like items[2].reviews[0].text
        parts = re.split(r'\.|\[|\]', p)
        parts = [x for x in parts if x]
        val = d
        for part in parts:
            try:
                if isinstance(val, list) and part.isdigit():
                    val = val[int(part)]
                elif isinstance(val, dict):
                    val = val.get(part)
                else:
                    return None
            except (IndexError, KeyError, TypeError):
                return None
        return val

    result = resolve_path(path, data)
    if result is None:
        return f"Error: path '{path}' not found"
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False)


def tool_lwt_list(lwt_steps: List[str]) -> str:
    """Show current LWT steps with indices."""
    if not lwt_steps:
        return "(empty)"
    lines = []
    for i, step in enumerate(lwt_steps):
        lines.append(f"{i}: {step}")
    return "\n".join(lines)


def tool_lwt_get(idx: int, lwt_steps: List[str]) -> str:
    """Get step at index."""
    if idx < 0 or idx >= len(lwt_steps):
        return f"Error: index {idx} out of range (0-{len(lwt_steps)-1})"
    return lwt_steps[idx]


def tool_lwt_set(idx: int, step: str, lwt_steps: List[str]) -> str:
    """Replace step at index with raw step string. Returns status."""
    if idx < 0 or idx >= len(lwt_steps):
        return f"Error: index {idx} out of range (0-{len(lwt_steps)-1})"
    lwt_steps[idx] = step
    return f"Replaced step at index {idx}"


def tool_lwt_set_prompt(idx: int, step_id: str, prompt: str, lwt_steps: List[str]) -> str:
    """Replace step at index with auto-formatted LLM call."""
    if idx < 0 or idx >= len(lwt_steps):
        return f"Error: index {idx} out of range (0-{len(lwt_steps)-1})"
    escaped_prompt = prompt.replace("'", "\\'")
    formatted_step = f"({step_id})=LLM('{escaped_prompt}')"
    lwt_steps[idx] = formatted_step
    return f"OK"


def tool_update_step(step_id: str, prompt: str, lwt_steps: List[str]) -> str:
    """Update step by ID (not index). Finds step with matching ID and updates it.

    This is safer than lwt_set_prompt - no index confusion possible.

    Args:
        step_id: Step identifier to find and update (e.g., "r7", "final")
        prompt: New prompt content

    Returns:
        "OK" on success, error message if step_id not found
    """
    # Find step with matching ID
    pattern = re.compile(rf'^\({re.escape(step_id)}\)=')
    for i, step in enumerate(lwt_steps):
        if pattern.match(step):
            escaped_prompt = prompt.replace("'", "\\'")
            lwt_steps[i] = f"({step_id})=LLM('{escaped_prompt}')"
            return "OK"

    available = [re.match(r'\((\w+)\)', s).group(1) for s in lwt_steps if re.match(r'\((\w+)\)', s)]
    return f"Error: step '{step_id}' not found. Available: {available}"


def tool_insert_step(step_id: str, prompt: str, lwt_steps: List[str]) -> str:
    """Insert a new step with given ID before the (final) step.

    Used for adding computation steps (e.g., hours range checks) during Phase 2.

    Args:
        step_id: New step identifier (e.g., "h2", "h6")
        prompt: The prompt content

    Returns:
        "OK" on success, error if step_id already exists
    """
    # Check if step ID already exists
    pattern = re.compile(rf'^\({re.escape(step_id)}\)=')
    for step in lwt_steps:
        if pattern.match(step):
            return f"Step '{step_id}' already exists. Use update_step to modify."

    escaped_prompt = prompt.replace("'", "\\'")
    new_step = f"({step_id})=LLM('{escaped_prompt}')"

    # Insert before (final) step
    for i, step in enumerate(lwt_steps):
        if '(final)=' in step:
            lwt_steps.insert(i, new_step)
            return "OK"

    # No (final) found, append
    lwt_steps.append(new_step)
    return "OK"


def tool_lwt_delete(idx: int, lwt_steps: List[str]) -> str:
    """Delete step at index. Returns status."""
    if idx < 0 or idx >= len(lwt_steps):
        return f"Error: index {idx} out of range (0-{len(lwt_steps)-1})"
    lwt_steps.pop(idx)
    return f"Deleted step at index {idx}"


def tool_lwt_insert(idx: int, step: str, lwt_steps: List[str]) -> str:
    """Insert raw step at index (or append if idx >= len). Returns status."""
    if idx < 0:
        return f"Error: index {idx} cannot be negative"
    # Clamp idx to valid range - append if beyond end
    if idx >= len(lwt_steps):
        lwt_steps.append(step)
        return f"Appended at index {len(lwt_steps) - 1}"
    lwt_steps.insert(idx, step)
    return f"Inserted at index {idx}"


def tool_lwt_insert_prompt(idx: int, step_id: str, prompt: str, lwt_steps: List[str]) -> str:
    """Insert auto-formatted LLM call at index.

    Args:
        idx: Index to insert at (or append if >= len)
        step_id: Step identifier (e.g., "r7", "final")
        prompt: The prompt content (without surrounding quotes/parens)
    """
    if idx < 0:
        return f"Error: index {idx} cannot be negative"

    # Escape any single quotes in the prompt
    escaped_prompt = prompt.replace("'", "\\'")
    # Build properly formatted step
    formatted_step = f"({step_id})=LLM('{escaped_prompt}')"

    if idx >= len(lwt_steps):
        lwt_steps.append(formatted_step)
        return f"OK: appended ({step_id})=LLM('...')"
    lwt_steps.insert(idx, formatted_step)
    return f"OK: inserted ({step_id})=LLM('...') at {idx}"


def tool_review_length(item_num: int, data: dict) -> str:
    """Return total character count of reviews for item."""
    items = data.get('items', data)
    item = items.get(str(item_num), {})
    reviews = item.get('reviews', [])
    total = sum(len(r.get('text', '')) for r in reviews if isinstance(r, dict))
    return str(total)


def tool_get_review_lengths(item_num: int, data: dict) -> str:
    """Return character count for EACH review in item.

    Returns JSON array of lengths, e.g., [1200, 5400, 800]
    """
    items = data.get('items', data)
    item = items.get(str(item_num), {})
    reviews = item.get('reviews', [])
    lengths = [len(r.get('text', '')) for r in reviews if isinstance(r, dict)]
    return json.dumps(lengths)


def tool_keyword_search(item_num: int, keyword: str, data: dict) -> str:
    """Search for keyword in item's reviews.

    Returns JSON with matches per review:
    {
        "matches": [
            {"review": 0, "positions": [1234, 5678], "length": 2400},
            {"review": 2, "positions": [100], "length": 800}
        ],
        "no_match_reviews": [1, 3],
        "total_matches": 3
    }
    """
    items = data.get('items', data)
    item = items.get(str(item_num), {})
    reviews = item.get('reviews', [])

    matches = []
    no_match = []
    total = 0
    keyword_lower = keyword.lower()

    for i, review in enumerate(reviews):
        if not isinstance(review, dict):
            continue
        text = review.get('text', '')
        text_lower = text.lower()
        length = len(text)

        # Find all positions of keyword (case-insensitive)
        positions = []
        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1

        if positions:
            matches.append({"review": i, "positions": positions, "length": length})
            total += len(positions)
        else:
            no_match.append(i)

    return json.dumps({
        "matches": matches,
        "no_match_reviews": no_match,
        "total_matches": total
    })


def tool_get_review_snippet(item_num: int, review_idx: int, start: int, length: int, data: dict) -> str:
    """Get a snippet of review text for inspection.

    Args:
        item_num: Item number (1-indexed)
        review_idx: Review index within item (0-indexed)
        start: Start position in text
        length: Number of characters to return

    Returns:
        Text snippet or error message
    """
    items = data.get('items', data)
    item = items.get(str(item_num), {})
    reviews = item.get('reviews', [])

    if review_idx < 0 or review_idx >= len(reviews):
        return f"Error: review index {review_idx} out of range (0-{len(reviews)-1})"

    text = reviews[review_idx].get('text', '')
    end = min(start + length, len(text))
    start = max(0, start)

    snippet = text[start:end]
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""

    return f"{prefix}{snippet}{suffix}"


# =============================================================================
# Phase 2 Context Expansion Tools
# =============================================================================

def tool_list_items(data: dict, resolved_conditions: list) -> str:
    """List all items with relevant attributes for the conditions.

    Args:
        data: Full data dict with 'items' key
        resolved_conditions: List of resolved condition dicts from Phase 1

    Returns:
        Formatted string showing item number and relevant attributes
    """
    items = data.get('items', data)

    # Extract field paths from conditions
    field_paths = set()
    def extract_paths(cond):
        if cond.get('type') == 'OR':
            for opt in cond.get('options', []):
                extract_paths(opt)
        elif cond.get('type') == 'AND':
            for sub in cond.get('conditions', []):
                extract_paths(sub)
        else:
            path = cond.get('path', '')
            if path:
                field_paths.add(path)

    for cond in resolved_conditions:
        extract_paths(cond)

    # Build output
    lines = []
    for key in sorted(items.keys(), key=lambda x: int(x)):
        item = items[key]
        attrs = item.get('attributes', {})
        categories = item.get('categories', [])

        parts = [f"Item {key}:"]
        for path in sorted(field_paths):
            # Parse path and get value
            val = _get_nested_value(item, path)
            # Simplify path for display
            short_path = path.split('.')[-1] if '.' in path else path
            parts.append(f"{short_path}={_format_val(val)}")

        lines.append(" ".join(parts))

    return "\n".join(lines)


def tool_check_item(item_num: int, data: dict, resolved_conditions: list) -> str:
    """Show item's full relevant attributes for the conditions.

    Args:
        item_num: Item number (1-indexed)
        data: Full data dict
        resolved_conditions: Resolved conditions from Phase 1

    Returns:
        Detailed view of item's relevant attributes
    """
    items = data.get('items', data)
    item = items.get(str(item_num), {})

    if not item:
        return f"Error: Item {item_num} not found"

    # Extract field paths
    field_paths = set()
    def extract_paths(cond):
        if cond.get('type') == 'OR':
            for opt in cond.get('options', []):
                extract_paths(opt)
        elif cond.get('type') == 'AND':
            for sub in cond.get('conditions', []):
                extract_paths(sub)
        else:
            path = cond.get('path', '')
            if path:
                field_paths.add(path)

    for cond in resolved_conditions:
        extract_paths(cond)

    # Build detailed output
    lines = [f"Item {item_num}:"]
    lines.append(f"  name: {item.get('name', 'Unknown')}")

    for path in sorted(field_paths):
        val = _get_nested_value(item, path)
        lines.append(f"  {path}: {_format_val(val)}")

    # Add categories if relevant
    if any('categories' in p for p in field_paths):
        lines.append(f"  categories: {item.get('categories', [])}")

    return "\n".join(lines)


def tool_drop_item(item_num: int, reason: str, dropped_items: set) -> str:
    """Mark item as dropped (non-candidate).

    Args:
        item_num: Item number to drop
        reason: Reason for dropping
        dropped_items: Set to track dropped items (mutated)

    Returns:
        Confirmation message
    """
    dropped_items.add(item_num)
    return f"Item {item_num} dropped: {reason}"


def tool_add_step(step_id: str, prompt: str, lwt_steps: list) -> str:
    """Add an LWT step for evaluating an item.

    Args:
        step_id: Step identifier (e.g., "c7" for item 7, "final" for aggregation)
        prompt: The prompt content (without LLM wrapper)
        lwt_steps: List of steps to modify

    Returns:
        Confirmation message
    """
    # Check if step already exists
    pattern = re.compile(rf'^\({re.escape(step_id)}\)=')
    for step in lwt_steps:
        if pattern.match(step):
            return f"Error: Step '{step_id}' already exists. Use update_step to modify."

    # Escape quotes and build step
    escaped_prompt = prompt.replace("'", "\\'")
    new_step = f"({step_id})=LLM('{escaped_prompt}')"

    # If adding 'final', append at end
    if step_id == 'final':
        lwt_steps.append(new_step)
    else:
        # Insert before 'final' if it exists, otherwise append
        for i, step in enumerate(lwt_steps):
            if '(final)=' in step:
                lwt_steps.insert(i, new_step)
                return f"Step {step_id} added"
        lwt_steps.append(new_step)

    return f"Step {step_id} added"


def _get_nested_value(item: dict, path: str):
    """Get value from nested dict using dot notation path."""
    parts = path.split('.')
    current = item
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
        if current is None:
            return None
    return current


def _format_val(val) -> str:
    """Format value for compact display."""
    if val is None:
        return "None"
    if isinstance(val, bool):
        return str(val)
    if isinstance(val, str):
        return repr(val)
    if isinstance(val, dict):
        # For nested dicts like Ambience, show only True values
        true_keys = [k for k, v in val.items() if v is True]
        false_count = sum(1 for v in val.values() if v is False)
        none_count = sum(1 for v in val.values() if v is None)
        if true_keys:
            return "{" + ",".join(f"{k}:True" for k in true_keys) + "}"
        return f"{{all False/None}}"
    if isinstance(val, list):
        if len(val) <= 3:
            return str(val)
        return f"[{val[0]}, {val[1]}, ... ({len(val)} items)]"
    return str(val)
