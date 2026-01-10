#!/usr/bin/env python3
"""
L2 Evaluation Framework - Tests LLM ability to compute derived metrics.

Usage:
    python explore/eval.py --task A --restaurant Acme
    python explore/eval.py --task all --restaurant all
"""

import json
import re
import sys
from pathlib import Path
from dataclasses import asdict
from typing import Dict, List, Any
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.llm import call_llm, configure
from tasks import TASK_REGISTRY, get_task, list_tasks

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = Path(__file__).parent / "output.json"

# Available restaurants
RESTAURANTS = [
    "Acme_Oyster_House__ab50qdW.jsonl",
    "Cochon_6a4gLLFS.jsonl",
    "Commander_s_Palace__C7QiQQc.jsonl",
    "Oceana_Grill_ac1AeYqs.jsonl",
    "Royal_House_VQcCL9Pi.jsonl",
]


SYSTEM_PROMPT_TEMPLATE = '''You are an expert data analyst. Your task is to analyze restaurant review data and compute specific metrics.

## INSTRUCTIONS

1. Read all the data carefully before computing answers
2. Show your intermediate calculations for each metric
3. Be precise with decimal places as specified in the task
4. Complete this analysis in a single response
5. Do NOT ask questions or request clarification - make reasonable assumptions for edge cases

## RESTAURANT METADATA

{restaurant_data}

## REVIEWS ({n_reviews} total)

{reviews_data}

## TASK

{task_prompt}

## OUTPUT FORMAT

After your analysis, output your final answers in EXACTLY this format:

===FINAL ANSWERS===
{output_fields}
===END===

Replace each field with your computed value. Do not include units or extra text in the values.
'''


def build_output_fields(ground_truth_class) -> str:
    """Build output field template from ground truth dataclass."""
    from dataclasses import fields as dc_fields
    type_map = {int: '[integer]', float: '[decimal]', str: '[string]'}
    return '\n'.join(f"{f.name.upper()}: {type_map.get(f.type, '[value]')}" for f in dc_fields(ground_truth_class))


def load_restaurant_data(filename: str, max_reviews: int = 100) -> tuple:
    """Load restaurant metadata and reviews as plain dicts."""
    with open(DATA_DIR / filename) as f:
        restaurant = json.loads(f.readline())
        reviews = [json.loads(line) for line in f]
    return restaurant, reviews[-max_reviews:] if max_reviews else reviews


def build_full_prompt(task_id: str, restaurant: dict, reviews: List[dict]) -> str:
    """Build full prompt with system template + task prompt."""
    task = get_task(task_id)

    # Format restaurant as full JSON dump
    restaurant_data = str(restaurant)

    # Format reviews as indexed JSON dumps
    reviews_data = '\n'.join(f"[R{i}] {r}" for i, r in enumerate(reviews, 1))

    # Get output fields from ground truth class
    output_fields = build_output_fields(task['ground_truth_class'])

    # Build full prompt
    return SYSTEM_PROMPT_TEMPLATE.format(
        restaurant_data=restaurant_data,
        n_reviews=len(reviews),
        reviews_data=reviews_data,
        task_prompt=task['prompt'],
        output_fields=output_fields,
    )


def detect_prompt_failure(response: str, parsed: Dict[str, Any], expected_fields: int) -> bool:
    """Return True if model failed due to prompt issues (not computation errors)."""
    numeric_count = sum(1 for v in parsed.values() if isinstance(v, (int, float)))
    if numeric_count >= expected_fields * 0.5:  # Got at least half the fields
        return False
    if '===FINAL' not in response.upper():
        return True
    if any(p in response.lower() for p in ['confirm', 'clarification', 'would you like']):
        return True
    return len(parsed) == 0


def parse_response(response: str) -> Dict[str, Any]:
    """Parse LLM response into field values."""
    parsed = {}

    # Extract final answers block
    final_block = response
    start_match = re.search(r'===\s*FINAL\s*ANSWERS\s*===', response, re.IGNORECASE)
    if start_match:
        remaining = response[start_match.end():]
        end_match = re.search(r'===\s*END\s*===', remaining, re.IGNORECASE)
        if end_match:
            final_block = remaining[:end_match.start()]
        else:
            final_block = remaining

    # Parse lines - handle both "KEY: value" and "KEY:\nvalue" formats
    lines = final_block.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if ':' not in line:
            continue

        key, value = line.split(':', 1)
        key = key.strip().upper()
        value = value.strip()

        # If value is empty, check next line
        if not value and i < len(lines):
            next_line = lines[i].strip()
            if next_line and ':' not in next_line:
                value = next_line
                i += 1

        if not value:
            continue

        # Try to parse as number
        try:
            if '.' in value:
                parsed[key] = float(value)
            else:
                parsed[key] = int(value)
        except ValueError:
            # Keep as string
            parsed[key] = value.strip('"\'')

    return parsed


def score_field(predicted: Any, expected: Any, tolerance: float = 0) -> float:
    """Score a single field."""
    if predicted is None:
        return 0.0

    # String comparison
    if isinstance(expected, str):
        return 1.0 if str(predicted).upper() == expected.upper() else 0.0

    # Numeric comparison
    try:
        pred_val = float(predicted)
        exp_val = float(expected)
        error = abs(pred_val - exp_val)

        if error <= tolerance:
            return 1.0
        else:
            max_error = max(abs(exp_val), 1.0)
            return max(0.0, 1.0 - (error - tolerance) / max_error)
    except (ValueError, TypeError):
        return 0.0


def evaluate_task(parsed: Dict, ground_truth: Any, tolerances: Dict[str, float] = None) -> Dict:
    """Evaluate parsed response against ground truth."""
    if tolerances is None:
        tolerances = {}

    gt_dict = asdict(ground_truth)
    results = {}

    for field, expected in gt_dict.items():
        field_upper = field.upper()
        predicted = parsed.get(field_upper)
        tolerance = tolerances.get(field, 0.05 if isinstance(expected, float) else 0)
        score = score_field(predicted, expected, tolerance)

        results[field] = {
            'expected': expected,
            'predicted': predicted,
            'score': score,
        }

    results['_total_score'] = sum(r['score'] for r in results.values() if isinstance(r, dict)) / len(gt_dict)

    return results


def run_task(task_id: str, restaurant_file: str, max_reviews: int = 100, verbose: bool = True, save_output: bool = True) -> Dict:
    """Run a single task on a single restaurant."""
    restaurant, reviews = load_restaurant_data(restaurant_file, max_reviews)
    task = get_task(task_id)

    # Print task instruction
    print(f"\n{'='*60}")
    print(f"Task {task_id}: {task['name']}")
    print(f"{'='*60}")
    print(task['prompt'])
    print()

    # Compute ground truth
    gt = task['compute_ground_truth'](reviews, restaurant)

    # Build full prompt: instructions + restaurant + reviews + task + output format
    prompt = build_full_prompt(task_id, restaurant, reviews)

    if verbose:
        print(f"Restaurant: {restaurant['name']}")
        print(f"Reviews: {len(reviews)}")
        print(f"Prompt length: {len(prompt):,} chars")

    response = call_llm(prompt)
    print("=== LLM output start ===")
    print(response)
    print("=== LLM output end ===")
    parsed = parse_response(response)
    expected_fields = len(asdict(gt))
    prompt_failure = detect_prompt_failure(response, parsed, expected_fields)
    results = evaluate_task(parsed, gt, task['tolerances'])

    # Add prompt failure info to results
    results['_prompt_failure'] = prompt_failure

    # Build output data
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'task': task_id,
        'task_name': task['name'],
        'restaurant': restaurant['name'],
        'n_reviews': len(reviews),
        'prompt': prompt,
        'llm_response': response,
        'ground_truth': asdict(gt),
        'parsed': parsed,
        'prompt_failure': prompt_failure,
        'results': results,
    }

    # Save output if requested
    if save_output:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)

    if verbose:
        if prompt_failure:
            print(f"\n⚠️  PROMPT FAILURE - fix the prompt, not a legitimate computational failure!")

        print(f"\n--- Results ---")
        for field, result in results.items():
            if field.startswith('_'):
                continue
            status = "✓" if result['score'] >= 0.9 else "~" if result['score'] >= 0.5 else "✗"
            print(f"  {field}: {result['expected']} vs {result['predicted']} ({result['score']:.2f}) {status}")

        print(f"\nTotal Score: {results['_total_score']:.3f}")
        if save_output:
            print(f"Output: {OUTPUT_FILE}")

    return output_data


def run_all_tasks(max_reviews: int = 100):
    """Run all tasks on all restaurants."""
    all_outputs = []
    scores = {}  # (restaurant, task) -> score

    for restaurant_file in RESTAURANTS:
        for task_id in list_tasks():
            try:
                output = run_task(task_id, restaurant_file, max_reviews, verbose=True, save_output=False)
                all_outputs.append(output)
                scores[(restaurant_file, task_id)] = output['results']['_total_score']
            except Exception as e:
                print(f"ERROR: {e}")
                scores[(restaurant_file, task_id)] = 0.0

    # Save and print summary
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({'timestamp': datetime.now().isoformat(), 'runs': all_outputs}, f, indent=2, default=str)

    tasks = list_tasks()
    print(f"\n{'='*60}\nSUMMARY\n{'='*60}")
    print(f"{'Restaurant':<20}" + "".join(f"{t:<8}" for t in tasks) + "Avg")

    for rf in RESTAURANTS:
        name = rf.split('_')[0]
        row = [scores.get((rf, t), 0) for t in tasks]
        print(f"{name:<20}" + "".join(f"{s:.2f}    " for s in row) + f"{sum(row)/len(row):.2f}")

    print(f"\nOutput: {OUTPUT_FILE}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="L2 Task Evaluation")
    parser.add_argument("--task", default="A", help="Task ID (A, B, C, D, F) or 'all'")
    parser.add_argument("--restaurant", default="Acme", help="Restaurant name prefix or 'all'")
    parser.add_argument("--max-reviews", type=int, default=100)
    args = parser.parse_args()

    configure(temperature=0.0)

    if args.task.lower() == 'all' or args.restaurant.lower() == 'all':
        run_all_tasks(args.max_reviews)
    else:
        restaurant_file = next((f for f in RESTAURANTS if args.restaurant.lower() in f.lower()), None)
        if not restaurant_file:
            sys.exit(f"Restaurant not found: {args.restaurant}\nAvailable: {RESTAURANTS}")
        run_task(args.task.upper(), restaurant_file, args.max_reviews)
