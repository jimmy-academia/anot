#!/usr/bin/env python3
"""Transform review_text queries to review_sentiment queries.

Changes 'has reviews mentioning X' to 'is praised for X' (positive sentiment).
Selects new gold restaurant that has positive sentiment for the topic.
"""

import json
import re
from collections import defaultdict
from pathlib import Path


def load_reviews(reviews_path: Path) -> dict:
    """Load reviews grouped by business_id."""
    reviews_by_biz = defaultdict(list)
    with open(reviews_path) as f:
        for line in f:
            r = json.loads(line)
            reviews_by_biz[r['business_id']].append(r)
    return reviews_by_biz


def load_restaurants(restaurants_path: Path) -> dict:
    """Load restaurants by business_id."""
    restaurants = {}
    with open(restaurants_path) as f:
        for line in f:
            r = json.loads(line)
            restaurants[r['business_id']] = r
    return restaurants


def get_sentiment_score(reviews: list, keywords: list) -> tuple:
    """Count positive (4-5 star) and negative (1-2 star) reviews mentioning keywords."""
    pattern = '|'.join(re.escape(k) for k in keywords)
    pos, neg = 0, 0
    for r in reviews:
        if re.search(pattern, r['text'], re.IGNORECASE):
            if r['stars'] >= 4:
                pos += 1
            elif r['stars'] <= 2:
                neg += 1
    return pos, neg


def check_item_meta(restaurant: dict, evidence: dict) -> bool:
    """Check if restaurant satisfies item_meta evidence."""
    path = evidence.get('path', [])
    val = restaurant
    for p in path:
        if isinstance(val, dict):
            val = val.get(p)
        else:
            return False
        if val is None:
            return False

    # Check condition
    if 'true' in evidence:
        expected = evidence['true']
        return str(val) == expected
    if 'contains' in evidence:
        return evidence['contains'] in str(val)
    return True


def find_best_gold(pattern: str, other_conditions: list, reviews_by_biz: dict,
                   restaurants: dict, original_gold: str) -> tuple:
    """Find best gold restaurant with positive sentiment for pattern.

    Returns (business_id, pos_count, neg_count) or None if not found.
    """
    candidates = []

    for biz_id, reviews in reviews_by_biz.items():
        pos, neg = get_sentiment_score(reviews, [pattern])

        # Must have positive sentiment (more positive than negative, or at least 2 positive)
        if pos <= neg or pos < 1:
            continue

        # Check other conditions (item_meta)
        restaurant = restaurants.get(biz_id, {})
        all_satisfied = True
        for cond in other_conditions:
            ev = cond.get('evidence', {})
            if ev.get('kind') == 'item_meta':
                if not check_item_meta(restaurant, ev):
                    all_satisfied = False
                    break

        if all_satisfied:
            # Score: positive count, prefer original gold if tied
            priority = 1 if biz_id == original_gold else 0
            candidates.append((biz_id, pos, neg, priority))

    if not candidates:
        return None

    # Sort by: positive count desc, priority desc, negative count asc
    candidates.sort(key=lambda x: (-x[1], -x[3], x[2]))
    best = candidates[0]
    return best[0], best[1], best[2]


def transform_request(request: dict, reviews_by_biz: dict, restaurants: dict) -> dict:
    """Transform a single request if it has review_text evidence."""
    structure = request.get('structure', {})
    args = structure.get('args', [])

    # Find review_text evidence and other conditions
    review_evidence_idx = None
    pattern = None
    other_conditions = []

    for i, arg in enumerate(args):
        evidence = arg.get('evidence', {})
        if evidence.get('kind') == 'review_text':
            review_evidence_idx = i
            pattern = evidence.get('pattern', '')
        else:
            other_conditions.append(arg)

    if review_evidence_idx is None:
        return request  # No review_text to transform

    original_gold = request.get('gold_restaurant', '')

    # Find best gold with positive sentiment
    result = find_best_gold(pattern, other_conditions, reviews_by_biz, restaurants, original_gold)

    if result is None:
        # No suitable gold found - skip transformation
        print(f"  WARNING: {request['id']} - no gold found for '{pattern}' with positive sentiment")
        return request

    new_gold, pos, neg = result

    # Transform text
    new_text = re.sub(
        rf"has reviews mentioning '{re.escape(pattern)}'",
        f"is praised for {pattern}",
        request['text']
    )

    # Transform evidence
    new_evidence = {
        'kind': 'review_sentiment',
        'topic': pattern,
        'sentiment': 'positive',
        'min_positive': 1
    }

    new_args = list(args)
    new_args[review_evidence_idx] = {**args[review_evidence_idx], 'evidence': new_evidence}
    new_structure = {**structure, 'args': new_args}

    transformed = {
        **request,
        'text': new_text,
        'structure': new_structure,
        'gold_restaurant': new_gold
    }

    # Log if gold changed
    if new_gold != original_gold:
        old_name = restaurants.get(original_gold, {}).get('name', original_gold[:8])
        new_name = restaurants.get(new_gold, {}).get('name', new_gold[:8])
        print(f"  {request['id']}: '{pattern}' gold changed: {old_name} -> {new_name} (pos={pos}, neg={neg})")
    else:
        print(f"  {request['id']}: '{pattern}' gold unchanged (pos={pos}, neg={neg})")

    return transformed


def main():
    data_dir = Path(__file__).parent.parent / 'philly_cafes'
    reviews_path = data_dir / 'reviews.jsonl'
    requests_path = data_dir / 'requests.jsonl'
    restaurants_path = data_dir / 'restaurants.jsonl'
    output_path = data_dir / 'requests_semantic.jsonl'

    print(f"Loading data...")
    reviews_by_biz = load_reviews(reviews_path)
    restaurants = load_restaurants(restaurants_path)
    print(f"Loaded {len(reviews_by_biz)} businesses, {len(restaurants)} restaurants")

    print(f"\nTransforming requests...")
    transformed_count = 0
    gold_changed_count = 0
    requests_out = []

    with open(requests_path) as f:
        for line in f:
            req = json.loads(line)
            original_gold = req.get('gold_restaurant')
            new_req = transform_request(req, reviews_by_biz, restaurants)

            if new_req != req:
                transformed_count += 1
                if new_req.get('gold_restaurant') != original_gold:
                    gold_changed_count += 1

            requests_out.append(new_req)

    print(f"\nSummary:")
    print(f"  Transformed: {transformed_count} requests")
    print(f"  Gold changed: {gold_changed_count} requests")

    # Write output
    with open(output_path, 'w') as f:
        for req in requests_out:
            f.write(json.dumps(req, ensure_ascii=False) + '\n')

    print(f"\nWritten to {output_path}")

    # Also update groundtruth.jsonl
    groundtruth_path = data_dir / 'groundtruth.jsonl'
    groundtruth_out_path = data_dir / 'groundtruth_semantic.jsonl'

    # Build mapping of request_id -> new gold
    gold_map = {req['id']: req['gold_restaurant'] for req in requests_out}

    with open(groundtruth_path) as f, open(groundtruth_out_path, 'w') as out:
        for line in f:
            gt = json.loads(line)
            req_id = gt['request_id']
            if req_id in gold_map:
                gt['gold_restaurant'] = gold_map[req_id]
            out.write(json.dumps(gt) + '\n')

    print(f"Updated groundtruth: {groundtruth_out_path}")


if __name__ == '__main__':
    main()
