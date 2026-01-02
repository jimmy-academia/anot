#!/usr/bin/env python3
"""Analyze Yelp data to identify unique attributes for ground truth filtering.

Usage:
    python preprocessing/scripts/analyze.py [selection_name]
    python preprocessing/scripts/analyze.py philly_cafes

Output: Prints analysis to stdout, saves JSON to preprocessing/output/{selection_name}/analysis.json
"""

import json
import sys
from collections import Counter
from pathlib import Path

OUTPUT_DIR = Path("preprocessing/output")


def load_jsonl(path):
    """Load JSONL file."""
    items = []
    with open(path) as f:
        for line in f:
            items.append(json.loads(line))
    return items


def analyze_restaurants(restaurants):
    """Analyze restaurant attributes."""
    results = {
        'count': len(restaurants),
        'attributes': {},
        'categories': {},
        'hours': {},
        'price': {},
        'wifi': {},
        'alcohol': {},
        'stars': {}
    }

    # Attribute coverage
    attr_counts = Counter()
    for r in restaurants:
        for k in r.get('attributes', {}).keys():
            attr_counts[k] += 1
    results['attributes']['coverage'] = dict(attr_counts.most_common(20))

    # Rare boolean attributes
    rare_bools = ['DogsAllowed', 'DriveThru', 'Corkage', 'HappyHour',
                  'WheelchairAccessible', 'GoodForDancing', 'CoatCheck',
                  'BYOB', 'BYOBCorkage', 'Smoking']
    results['attributes']['rare'] = {}
    for attr in rare_bools:
        count = sum(1 for r in restaurants if r.get('attributes', {}).get(attr) == 'True')
        if count > 0:
            results['attributes']['rare'][attr] = count

    # Price range
    for r in restaurants:
        price = r.get('attributes', {}).get('RestaurantsPriceRange2')
        if price:
            results['price'][price] = results['price'].get(price, 0) + 1

    # WiFi
    for r in restaurants:
        wifi = r.get('attributes', {}).get('WiFi')
        if wifi:
            # Normalize values
            wifi_norm = wifi.replace("u'", "").replace("'", "")
            results['wifi'][wifi_norm] = results['wifi'].get(wifi_norm, 0) + 1

    # Alcohol
    for r in restaurants:
        alc = r.get('attributes', {}).get('Alcohol')
        if alc:
            alc_norm = alc.replace("u'", "").replace("'", "")
            results['alcohol'][alc_norm] = results['alcohol'].get(alc_norm, 0) + 1

    # Categories
    all_cats = []
    for r in restaurants:
        cats = r.get('categories', '').split(',')
        all_cats.extend([c.strip() for c in cats if c.strip()])
    cat_counts = Counter(all_cats)
    results['categories']['rare'] = {c: cnt for c, cnt in cat_counts.items() if 1 <= cnt <= 5}
    results['categories']['common'] = dict(cat_counts.most_common(15))

    # Hours patterns
    closed_monday = 0
    late_night = set()
    early_open = set()

    for r in restaurants:
        hrs = r.get('hours', {})
        if not hrs:
            continue

        name = r.get('name', r.get('business_id', 'unknown'))

        if 'Monday' not in hrs:
            closed_monday += 1

        for day, times in hrs.items():
            if times and '-' in times:
                try:
                    open_t, close_t = times.split('-')
                    oh, _ = map(int, open_t.split(':'))
                    ch, _ = map(int, close_t.split(':'))

                    if ch >= 22 or ch < 6:
                        late_night.add(name)
                    if oh < 8:
                        early_open.add(name)
                except:
                    pass

    results['hours'] = {
        'closed_monday': closed_monday,
        'late_night': len(late_night),
        'early_open': len(early_open)
    }

    # Stars
    for r in restaurants:
        stars = r.get('stars')
        if stars:
            results['stars'][str(stars)] = results['stars'].get(str(stars), 0) + 1

    return results


def analyze_reviews(reviews):
    """Analyze review data."""
    results = {
        'count': len(reviews),
        'stars': {},
        'elite_count': 0,
        'high_social_count': 0,
        'engagement': {},
        'date_range': {},
        'length_stats': {}
    }

    # Stars distribution
    for r in reviews:
        stars = r.get('stars')
        if stars:
            key = str(float(stars))
            results['stars'][key] = results['stars'].get(key, 0) + 1

    # Elite users
    results['elite_count'] = sum(1 for r in reviews if r.get('user', {}).get('elite'))

    # High-social users (100+ friends)
    for r in reviews:
        friends = r.get('user', {}).get('friends', '')
        if friends and friends != 'None':
            if len(str(friends).split(',')) >= 100:
                results['high_social_count'] += 1

    # Engagement stats
    useful = [r.get('useful', 0) for r in reviews]
    funny = [r.get('funny', 0) for r in reviews]
    cool = [r.get('cool', 0) for r in reviews]

    results['engagement'] = {
        'useful_max': max(useful) if useful else 0,
        'useful_avg': round(sum(useful) / len(useful), 1) if useful else 0,
        'funny_max': max(funny) if funny else 0,
        'funny_avg': round(sum(funny) / len(funny), 1) if funny else 0,
        'cool_max': max(cool) if cool else 0,
        'cool_avg': round(sum(cool) / len(cool), 1) if cool else 0
    }

    # Date range
    dates = sorted([r.get('date', '') for r in reviews if r.get('date')])
    if dates:
        results['date_range'] = {
            'earliest': dates[0],
            'latest': dates[-1],
            'recent_2020': sum(1 for d in dates if d >= '2020')
        }

    # Review length
    lengths = [len(r.get('text', '')) for r in reviews]
    if lengths:
        results['length_stats'] = {
            'min': min(lengths),
            'max': max(lengths),
            'avg': round(sum(lengths) / len(lengths))
        }

    return results


def print_summary(rest_results, rev_results):
    """Print formatted summary to stdout."""
    print(f"\n{'='*60}")
    print(f"RESTAURANT ANALYSIS ({rest_results['count']} restaurants)")
    print(f"{'='*60}")

    print("\nRare Attributes (good for GT filtering):")
    for attr, count in sorted(rest_results['attributes']['rare'].items(), key=lambda x: x[1]):
        pct = count / rest_results['count'] * 100
        print(f"  {attr}=True: {count} ({pct:.1f}%)")

    print("\nPrice Distribution:")
    for price, count in sorted(rest_results['price'].items()):
        print(f"  Price {price}: {count}")

    print("\nWiFi Distribution:")
    for wifi, count in sorted(rest_results['wifi'].items(), key=lambda x: -x[1]):
        print(f"  {wifi}: {count}")

    print("\nRare Categories (1-5 restaurants):")
    rare_cats = list(rest_results['categories']['rare'].items())[:10]
    for cat, count in sorted(rare_cats, key=lambda x: x[1]):
        print(f"  {cat}: {count}")

    print("\nHours Patterns:")
    for k, v in rest_results['hours'].items():
        print(f"  {k}: {v}")

    print(f"\n{'='*60}")
    print(f"REVIEW ANALYSIS ({rev_results['count']} reviews)")
    print(f"{'='*60}")

    elite_pct = rev_results['elite_count'] / rev_results['count'] * 100 if rev_results['count'] else 0
    print(f"\nElite reviews: {rev_results['elite_count']} ({elite_pct:.0f}%)")
    print(f"High-social users (100+ friends): {rev_results['high_social_count']}")

    if rev_results['date_range']:
        print(f"Date range: {rev_results['date_range'].get('earliest', 'N/A')} to {rev_results['date_range'].get('latest', 'N/A')}")
        print(f"Recent (2020+): {rev_results['date_range'].get('recent_2020', 0)}")

    print(f"\nEngagement:")
    eng = rev_results['engagement']
    print(f"  Useful: max={eng.get('useful_max', 0)}, avg={eng.get('useful_avg', 0)}")
    print(f"  Funny: max={eng.get('funny_max', 0)}, avg={eng.get('funny_avg', 0)}")
    print(f"  Cool: max={eng.get('cool_max', 0)}, avg={eng.get('cool_avg', 0)}")

    if rev_results['length_stats']:
        ls = rev_results['length_stats']
        print(f"\nReview Length: min={ls['min']}, max={ls['max']}, avg={ls['avg']}")


def main():
    # Get selection name (default: philly_cafes)
    selection_name = sys.argv[1] if len(sys.argv) > 1 else 'philly_cafes'
    selection_dir = OUTPUT_DIR / selection_name

    if not selection_dir.exists():
        print(f"Error: Selection directory not found: {selection_dir}")
        print(f"Available selections: {[d.name for d in OUTPUT_DIR.iterdir() if d.is_dir()]}")
        sys.exit(1)

    rest_path = selection_dir / 'restaurants.jsonl'
    rev_path = selection_dir / 'reviews.jsonl'

    print(f"Analyzing selection: {selection_name}")
    print(f"Loading {rest_path}...")
    restaurants = load_jsonl(rest_path)

    print(f"Loading {rev_path}...")
    reviews = load_jsonl(rev_path)

    print("Analyzing...")
    rest_results = analyze_restaurants(restaurants)
    rev_results = analyze_reviews(reviews)

    # Print summary
    print_summary(rest_results, rev_results)

    # Save full results as JSON
    output = {'restaurants': rest_results, 'reviews': rev_results}
    out_path = selection_dir / 'analysis.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n\nFull results saved to {out_path}")


if __name__ == '__main__':
    main()
