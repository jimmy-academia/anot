#!/usr/bin/env python3
"""Rewrite request texts to explicitly signal all groundtruth conditions.

Problem: Original request texts may not mention all conditions required by groundtruth.
Example: "I need a cafe with a drive-thru" but groundtruth also requires HasTV=False.

Solution: Rewrite texts to explicitly mention ALL conditions in the structure field,
ensuring 1-to-1 mapping between text signals and groundtruth conditions.

Usage:
    python -m preprocessing.rewrite_requests {dataset_name}
    python -m preprocessing.rewrite_requests philly_cafes --dry-run
    python -m preprocessing.rewrite_requests philly_cafes --analyze
"""

import json
import argparse
import sys
from pathlib import Path


# Mapping from condition evidence to human-readable text
CONDITION_TEMPLATES = {
    # Attribute conditions (item_meta)
    ("attributes", "DriveThru", "True"): "with a drive-thru",
    ("attributes", "DriveThru", "False"): "without a drive-thru",
    ("attributes", "GoodForKids", "True"): "that's kid-friendly",
    ("attributes", "GoodForKids", "False"): "that's not aimed at kids",
    ("attributes", "HasTV", "True"): "with TVs",
    ("attributes", "HasTV", "False"): "without TVs",
    ("attributes", "DogsAllowed", "True"): "that's dog-friendly",
    ("attributes", "DogsAllowed", "False"): "that doesn't allow dogs",
    ("attributes", "BikeParking", "True"): "with bike parking",
    ("attributes", "BikeParking", "False"): "without bike parking",
    ("attributes", "OutdoorSeating", "True"): "with outdoor seating",
    ("attributes", "OutdoorSeating", "False"): "indoor-only (no outdoor seating)",
    ("attributes", "RestaurantsReservations", "True"): "that takes reservations",
    ("attributes", "RestaurantsReservations", "False"): "with no reservations needed",
    ("attributes", "RestaurantsGoodForGroups", "True"): "that's good for groups",
    ("attributes", "RestaurantsGoodForGroups", "False"): "not suited for groups",
    ("attributes", "RestaurantsTakeOut", "True"): "with takeout available",
    ("attributes", "RestaurantsTakeOut", "False"): "without takeout",
    ("attributes", "RestaurantsDelivery", "True"): "that offers delivery",
    ("attributes", "RestaurantsDelivery", "False"): "without delivery",
    ("attributes", "BusinessAcceptsCreditCards", "True"): "that accepts credit cards",
    ("attributes", "BusinessAcceptsCreditCards", "False"): "cash only",
    ("attributes", "WheelchairAccessible", "True"): "that's wheelchair accessible",
    ("attributes", "WheelchairAccessible", "False"): "not wheelchair accessible",
    ("attributes", "CoatCheck", "True"): "with coat check",
    ("attributes", "CoatCheck", "False"): "without coat check",
    ("attributes", "BYOB", "True"): "that's BYOB",
    ("attributes", "BYOB", "False"): "that's not BYOB",
    ("attributes", "Corkage", "True"): "with corkage allowed",
    ("attributes", "HappyHour", "True"): "with happy hour",
    ("attributes", "HappyHour", "False"): "without happy hour",

    # WiFi conditions
    ("attributes", "WiFi", "u'free'"): "with free WiFi",
    ("attributes", "WiFi", "u'no'"): "without WiFi",
    ("attributes", "WiFi", "u'paid'"): "with paid WiFi",

    # Noise level conditions
    ("attributes", "NoiseLevel", "u'quiet'"): "that's quiet",
    ("attributes", "NoiseLevel", "u'average'"): "with average noise level",
    ("attributes", "NoiseLevel", "u'loud'"): "that's loud and lively",
    ("attributes", "NoiseLevel", "u'very_loud'"): "that's very loud",

    # Alcohol conditions
    ("attributes", "Alcohol", "u'full_bar'"): "with a full bar",
    ("attributes", "Alcohol", "u'beer_and_wine'"): "with beer and wine",
    ("attributes", "Alcohol", "u'none'"): "without alcohol",

    # Price range conditions
    ("attributes", "RestaurantsPriceRange2", "1"): "that's budget-friendly",
    ("attributes", "RestaurantsPriceRange2", "2"): "that's mid-priced",
    ("attributes", "RestaurantsPriceRange2", "3"): "that's upscale",
    ("attributes", "RestaurantsPriceRange2", "4"): "that's high-end",
}

# Ambience contains patterns
AMBIENCE_TEMPLATES = {
    "'hipster': True": "with a hipster vibe",
    "'trendy': True": "that's trendy",
    "'casual': True": "with a casual atmosphere",
    "'romantic': True": "with a romantic atmosphere",
    "'intimate': True": "with an intimate atmosphere",
    "'classy': True": "with a classy atmosphere",
    "'upscale': True": "with an upscale atmosphere",
    "'divey': True": "with a divey atmosphere",
    "'touristy': True": "that's touristy",
}

# GoodForMeal contains patterns
MEAL_TEMPLATES = {
    "'breakfast': True": "good for breakfast",
    "'brunch': True": "good for brunch",
    "'lunch': True": "good for lunch",
    "'dinner': True": "good for dinner",
    "'latenight': True": "good for late night",
    "'dessert': True": "good for dessert",
}


def condition_to_text(condition: dict) -> str:
    """Convert a single condition to human-readable text."""
    evidence = condition.get("evidence", {})
    kind = evidence.get("kind")

    if kind == "item_meta":
        path = tuple(evidence.get("path", []))

        # Handle "true" value conditions
        if "true" in evidence:
            key = (*path, evidence["true"])
            if key in CONDITION_TEMPLATES:
                return CONDITION_TEMPLATES[key]
            # Fallback for unknown attribute
            attr = path[-1] if path else "unknown"
            return f"with {attr}={evidence['true']}"

        # Handle "contains" conditions (Ambience, GoodForMeal)
        if "contains" in evidence:
            contains = evidence["contains"]
            if "Ambience" in path:
                if contains in AMBIENCE_TEMPLATES:
                    return AMBIENCE_TEMPLATES[contains]
                return f"with ambience containing {contains}"
            if "GoodForMeal" in path:
                if contains in MEAL_TEMPLATES:
                    return MEAL_TEMPLATES[contains]
                clean = contains.replace("'", "").replace(": True", "")
                return clean
            return f"where {path[-1]} contains {contains}"

    elif kind == "review_text":
        pattern = evidence.get("pattern", "")
        return f"where reviews mention '{pattern}'"

    elif kind == "item_meta_hours":
        day = evidence.get("day", "")
        hour = evidence.get("hour", "")
        return f"open on {day} at {hour}"

    # Fallback
    return f"[unknown condition: {condition}]"


def rewrite_request(request: dict) -> dict:
    """Rewrite a single request to signal all conditions."""
    structure = request.get("structure", {})
    conditions = structure.get("args", [])

    # Convert all conditions to text
    condition_texts = [condition_to_text(c) for c in conditions]

    # Build new text
    new_text = "Looking for a cafe " + ", ".join(condition_texts)

    # Update request with new text
    new_request = request.copy()
    new_request["text"] = new_text
    # Remove original_text if present
    new_request.pop("original_text", None)

    return new_request


def analyze_missing_signals(requests: list) -> dict:
    """Analyze which conditions are not signaled in original request texts."""
    results = {
        "total_conditions": 0,
        "missing_signals": 0,
        "by_request": [],
    }

    for req in requests:
        text = req.get("text", "").lower()
        structure = req.get("structure", {})
        conditions = structure.get("args", [])

        missing = []
        for cond in conditions:
            evidence = cond.get("evidence", {})
            kind = evidence.get("kind")
            results["total_conditions"] += 1

            # Check if condition is signaled in text
            signaled = False

            if kind == "item_meta":
                path = evidence.get("path", [])
                attr = path[-1] if path else ""
                value = evidence.get("true", evidence.get("contains", ""))

                # Simple keyword check
                keywords = [attr.lower(), value.lower().replace("u'", "").replace("'", "")]
                if any(kw in text for kw in keywords if len(kw) > 2):
                    signaled = True

            elif kind == "review_text":
                pattern = evidence.get("pattern", "").lower()
                if pattern in text:
                    signaled = True

            elif kind == "item_meta_hours":
                day = evidence.get("day", "").lower()
                if day in text:
                    signaled = True

            if not signaled:
                missing.append(cond.get("aspect", str(evidence)))
                results["missing_signals"] += 1

        if missing:
            results["by_request"].append({
                "id": req.get("id"),
                "text": req.get("text")[:60] + "...",
                "missing": missing,
            })

    return results


def main():
    parser = argparse.ArgumentParser(description="Rewrite request texts to signal all conditions")
    parser.add_argument("dataset", help="Dataset name (e.g., philly_cafes)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--analyze", action="store_true", help="Analyze missing signals only")
    parser.add_argument("--output", "-o", help="Output filename (default: requests_v2.jsonl)")
    args = parser.parse_args()

    # Find input file
    data_dir = Path(__file__).parent.parent / "data" / args.dataset
    input_file = data_dir / "requests.jsonl"

    if not input_file.exists():
        print(f"Error: {input_file} not found", file=sys.stderr)
        sys.exit(1)

    # Read requests
    requests = []
    with open(input_file) as f:
        for line in f:
            if line.strip():
                requests.append(json.loads(line))

    print(f"Read {len(requests)} requests from {input_file}")

    # Analyze mode
    if args.analyze:
        results = analyze_missing_signals(requests)
        print(f"\nAnalysis:")
        print(f"  Total conditions: {results['total_conditions']}")
        print(f"  Missing signals: {results['missing_signals']} ({100*results['missing_signals']/results['total_conditions']:.1f}%)")
        print(f"\nRequests with missing signals:")
        for r in results["by_request"]:
            print(f"  {r['id']}: {r['text']}")
            print(f"    Missing: {', '.join(r['missing'])}")
        return

    # Rewrite requests
    rewritten = []
    for req in requests:
        new_req = rewrite_request(req)
        rewritten.append(new_req)

        if args.dry_run:
            old_text = req.get("text", "")
            new_text = new_req.get("text", "")
            if old_text != new_text:
                print(f"\n{req.get('id')}:")
                print(f"  OLD: {old_text}")
                print(f"  NEW: {new_text}")

    if args.dry_run:
        print(f"\n[DRY RUN] Would write {len(rewritten)} requests")
        return

    # Write output (default to requests.jsonl to replace original)
    output_file = data_dir / (args.output or "requests.jsonl")
    with open(output_file, "w") as f:
        for req in rewritten:
            f.write(json.dumps(req) + "\n")

    print(f"Wrote {len(rewritten)} requests to {output_file}")


if __name__ == "__main__":
    main()
