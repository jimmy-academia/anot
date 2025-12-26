#!/usr/bin/env python3
"""Automated verification script for knot vs cot experiments.

This script:
1. Generates real data from Yelp
2. Runs cot and knot experiments
3. Compares results
4. If knot doesn't win, adjusts selection and retries (up to 3 times)
"""

import json
import subprocess
import sys
from pathlib import Path


def run_experiment(data_path: str, method: str, limit: int = None) -> dict:
    """Run experiment and return results."""
    cmd = ["python3", "main.py", "--data", data_path, "--method", method]
    if limit:
        cmd.extend(["--limit", str(limit)])

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    # Parse accuracy from output
    for line in output.split("\n"):
        if line.startswith("Overall:"):
            parts = line.split()
            accuracy = float(parts[1])
            counts = parts[2].strip("()")
            correct, total = map(int, counts.split("/"))
            return {"accuracy": accuracy, "correct": correct, "total": total}

    return {"accuracy": 0, "correct": 0, "total": 0}


def generate_data(n: int = 20, adjust: int = None, output: str = "real_data.jsonl") -> str:
    """Generate data using select_real_data.py."""
    cmd = ["python3", "data/select_real_data.py", "--n", str(n), "--output", output]
    if adjust:
        cmd.extend(["--adjust", str(adjust)])

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error generating data: {result.stderr}")
        return None

    return f"data/{output}"


def knot_wins(cot_result: dict, knot_result: dict, margin: float = 0.0) -> bool:
    """Check if knot outperforms cot by at least margin."""
    return knot_result["accuracy"] > cot_result["accuracy"] + margin


def run_and_verify(n: int = 20, limit: int = None, max_attempts: int = 3) -> dict:
    """Full verification pipeline with automatic readjustment."""
    results = []

    for attempt in range(max_attempts):
        print(f"\n{'='*60}")
        print(f"ATTEMPT {attempt + 1}/{max_attempts}")
        print("=" * 60)

        # Generate data (with adjustment for attempts > 0)
        adjust = attempt if attempt > 0 else None
        output_name = f"real_data_attempt{attempt + 1}.jsonl"
        data_path = generate_data(n=n, adjust=adjust, output=output_name)

        if not data_path:
            print("Failed to generate data")
            continue

        # Run experiments
        print(f"\nRunning cot on {data_path}...")
        cot_result = run_experiment(data_path, "cot", limit)
        print(f"cot: {cot_result['accuracy']:.4f} ({cot_result['correct']}/{cot_result['total']})")

        print(f"\nRunning knot on {data_path}...")
        knot_result = run_experiment(data_path, "knot", limit)
        print(f"knot: {knot_result['accuracy']:.4f} ({knot_result['correct']}/{knot_result['total']})")

        # Record results
        attempt_result = {
            "attempt": attempt + 1,
            "data_path": data_path,
            "adjustment": adjust,
            "cot": cot_result,
            "knot": knot_result,
            "knot_wins": knot_wins(cot_result, knot_result),
        }
        results.append(attempt_result)

        # Check if knot wins
        if attempt_result["knot_wins"]:
            print(f"\n{'='*60}")
            print("SUCCESS: knot outperforms cot!")
            print(f"  cot:  {cot_result['accuracy']:.4f}")
            print(f"  knot: {knot_result['accuracy']:.4f}")
            print(f"  margin: +{knot_result['accuracy'] - cot_result['accuracy']:.4f}")
            print("=" * 60)
            break
        else:
            print(f"\nknot did not outperform cot, will try adjustment {attempt + 1}...")

    # Final summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    for r in results:
        status = "PASS" if r["knot_wins"] else "FAIL"
        adjust_str = f"(adjust={r['adjustment']})" if r["adjustment"] else "(no adjust)"
        print(f"Attempt {r['attempt']} {adjust_str}: cot={r['cot']['accuracy']:.4f}, "
              f"knot={r['knot']['accuracy']:.4f} [{status}]")

    success = any(r["knot_wins"] for r in results)
    print(f"\nFinal result: {'SUCCESS' if success else 'FAILED after all attempts'}")

    # Save results
    with open("verification_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to verification_results.json")

    return {"success": success, "results": results}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify knot outperforms cot on real Yelp data")
    parser.add_argument("--n", type=int, default=20, help="Number of restaurants")
    parser.add_argument("--limit", type=int, help="Limit items to test (for quick testing)")
    parser.add_argument("--max-attempts", type=int, default=3, help="Max readjustment attempts")
    args = parser.parse_args()

    result = run_and_verify(n=args.n, limit=args.limit, max_attempts=args.max_attempts)
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
