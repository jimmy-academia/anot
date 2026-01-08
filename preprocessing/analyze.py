#!/usr/bin/env python3
"""Analyze Yelp data to identify unique attributes for ground truth filtering.

Usage:
    python -m preprocessing.analyze [selection_name]
    python -m preprocessing.analyze philly_cafes

Output: Prints analysis to stdout, saves JSON to preprocessing/output/{selection_name}/analysis.json
"""

import ast
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, stdev

OUTPUT_DIR = Path("preprocessing/output")


def parse_dict_attr(attr_str):
    """Parse dict-like attribute string: "{'key': True, ...}" -> dict."""
    if not attr_str:
        return {}
    try:
        # Handle both Python-style and u'string' formats
        cleaned = attr_str.replace("u'", "'").replace("True", "True").replace("False", "False")
        return ast.literal_eval(cleaned)
    except (ValueError, SyntaxError):
        return {}


def normalize_attr(attr_str):
    """Normalize attribute value: "u'free'" -> "free"."""
    if not attr_str:
        return None
    return attr_str.replace("u'", "").replace("'", "").strip()


def load_jsonl(path):
    """Load JSONL file."""
    items = []
    with open(path) as f:
        for line in f:
            items.append(json.loads(line))
    return items


def analyze_restaurants(restaurants):
    """Analyze restaurant attributes comprehensively."""
    n = len(restaurants)
    results = {
        'count': n,
        'distributions': {},
        'rare_features': {},
        'categories': {},
        'hours': {},
    }

    # --- Distribution Counters ---
    noise_level = Counter()
    outdoor_seating = Counter()
    good_for_kids = Counter()
    good_for_groups = Counter()
    reservations = Counter()
    delivery = Counter()
    takeout = Counter()
    price_range = Counter()
    wifi = Counter()
    alcohol = Counter()
    stars = Counter()

    # Ambience and Parking breakdowns
    ambience_counts = Counter()
    parking_counts = Counter()

    # Rare boolean attributes tracking
    rare_bools = ['DogsAllowed', 'DriveThru', 'Corkage', 'HappyHour',
                  'WheelchairAccessible', 'GoodForDancing', 'CoatCheck',
                  'BYOB', 'BYOBCorkage', 'Smoking', 'Caters', 'HasTV', 'BikeParking']
    rare_tracking = {attr: [] for attr in rare_bools}

    for r in restaurants:
        attrs = r.get('attributes') or {}
        bid = r.get('business_id')

        # NoiseLevel
        nl = normalize_attr(attrs.get('NoiseLevel'))
        if nl:
            noise_level[nl] += 1

        # Boolean distributions
        os = attrs.get('OutdoorSeating')
        if os:
            outdoor_seating[os] += 1

        gfk = attrs.get('GoodForKids')
        if gfk:
            good_for_kids[gfk] += 1

        gfg = attrs.get('RestaurantsGoodForGroups')
        if gfg:
            good_for_groups[gfg] += 1

        res = attrs.get('RestaurantsReservations')
        if res:
            reservations[res] += 1

        dlv = attrs.get('RestaurantsDelivery')
        if dlv:
            delivery[dlv] += 1

        to = attrs.get('RestaurantsTakeOut')
        if to:
            takeout[to] += 1

        # Price range
        pr = attrs.get('RestaurantsPriceRange2')
        if pr:
            price_range[pr] += 1

        # WiFi
        wf = normalize_attr(attrs.get('WiFi'))
        if wf:
            wifi[wf] += 1

        # Alcohol
        alc = normalize_attr(attrs.get('Alcohol'))
        if alc:
            alcohol[alc] += 1

        # Stars
        st = r.get('stars')
        if st:
            stars[str(st)] += 1

        # Parse Ambience dict
        amb = parse_dict_attr(attrs.get('Ambience'))
        for k, v in amb.items():
            if v:
                ambience_counts[k] += 1

        # Parse BusinessParking dict
        park = parse_dict_attr(attrs.get('BusinessParking'))
        for k, v in park.items():
            if v:
                parking_counts[k] += 1

        # Track rare boolean attributes
        for attr in rare_bools:
            if attrs.get(attr) == 'True':
                rare_tracking[attr].append(bid)

    # Store distributions
    results['distributions'] = {
        'noise_level': dict(noise_level),
        'outdoor_seating': dict(outdoor_seating),
        'good_for_kids': dict(good_for_kids),
        'good_for_groups': dict(good_for_groups),
        'reservations': dict(reservations),
        'delivery': dict(delivery),
        'takeout': dict(takeout),
        'price_range': dict(price_range),
        'wifi': dict(wifi),
        'alcohol': dict(alcohol),
        'stars': dict(stars),
        'ambience': dict(ambience_counts.most_common()),
        'parking': dict(parking_counts.most_common()),
    }

    # Store rare features (with business IDs for selection)
    results['rare_features'] = {attr: bids for attr, bids in rare_tracking.items() if 0 < len(bids) <= 10}

    # Categories
    all_cats = []
    for r in restaurants:
        cats = r.get('categories', '').split(',')
        all_cats.extend([c.strip() for c in cats if c.strip()])
    cat_counts = Counter(all_cats)
    results['categories'] = {
        'rare': {c: cnt for c, cnt in cat_counts.items() if 1 <= cnt <= 5},
        'common': dict(cat_counts.most_common(15))
    }

    # Hours patterns
    closed_monday = []
    late_night = []
    early_open = []

    for r in restaurants:
        hrs = r.get('hours') or {}
        bid = r.get('business_id')
        if not hrs:
            continue

        if 'Monday' not in hrs:
            closed_monday.append(bid)

        for day, times in hrs.items():
            if times and '-' in times:
                try:
                    open_t, close_t = times.split('-')
                    oh, _ = map(int, open_t.split(':'))
                    ch, _ = map(int, close_t.split(':'))
                    if ch >= 22 or ch < 6:
                        if bid not in late_night:
                            late_night.append(bid)
                    if oh < 8:
                        if bid not in early_open:
                            early_open.append(bid)
                except (ValueError, TypeError):
                    pass

    results['hours'] = {
        'closed_monday': len(closed_monday),
        'late_night': len(late_night),
        'early_open': len(early_open),
    }

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


# Stopwords and generic phrases to filter out
STOPWORDS = {
    'the', 'and', 'was', 'were', 'for', 'with', 'this', 'that', 'have', 'had',
    'are', 'but', 'not', 'you', 'all', 'can', 'her', 'his', 'from', 'they',
    'been', 'has', 'will', 'would', 'could', 'what', 'there', 'their', 'out',
    'about', 'just', 'get', 'got', 'like', 'really', 'very', 'when', 'also',
    'our', 'back', 'some', 'which', 'them', 'than', 'then', 'into', 'your',
    'here', 'come', 'came', 'went', 'going', 'one', 'two', 'first', 'time',
    'food', 'place', 'good', 'great', 'nice', 'love', 'best', 'definitely',
    'always', 'ever', 'even', 'much', 'well', 'really', 'pretty', 'amazing'
}

GENERIC_BIGRAMS = {
    'really good', 'very good', 'so good', 'pretty good',
    'food was', 'service was', 'place was', 'it was',
    'came here', 'come here', 'came back', 'come back', 'will come',
    'going back', 'went here', 'tried the', 'ordered the', 'had the',
    'highly recommend', 'would recommend', 'definitely recommend',
    'next time', 'first time', 'every time', 'last time',
    'can not', 'could not', 'would not', 'did not', 'do not',
}


def analyze_review_text(reviews, min_mentions=3, min_restaurants=3, max_restaurants=5):
    """Find characteristic phrases: frequent within a small cluster of restaurants.

    Args:
        reviews: List of review dicts
        min_mentions: Minimum times a phrase must appear in a restaurant's reviews
        min_restaurants: Minimum restaurants that must share the phrase
        max_restaurants: Maximum restaurants a phrase can appear in
    """
    # Group reviews by business_id
    reviews_by_biz = defaultdict(list)
    biz_names = {}
    for r in reviews:
        bid = r['business_id']
        reviews_by_biz[bid].append(r.get('text', ''))

    # Count n-gram frequency per restaurant (not just presence)
    biz_ngram_counts = {}  # {biz_id: {ngram: count}}
    for biz_id, texts in reviews_by_biz.items():
        ngram_counts = Counter()
        for text in texts:
            words = re.findall(r'\b[a-z]+\b', text.lower())
            words = [w for w in words if w not in STOPWORDS and len(w) >= 3]

            # Bigrams
            for i in range(len(words) - 1):
                bg = f"{words[i]} {words[i+1]}"
                if bg not in GENERIC_BIGRAMS:
                    ngram_counts[bg] += 1
            # Trigrams
            for i in range(len(words) - 2):
                tg = f"{words[i]} {words[i+1]} {words[i+2]}"
                ngram_counts[tg] += 1

        # Only keep phrases mentioned min_mentions+ times
        biz_ngram_counts[biz_id] = {ng: cnt for ng, cnt in ngram_counts.items() if cnt >= min_mentions}

    # Find which restaurants have each phrase (only counting frequent ones)
    ngram_to_bizs = defaultdict(dict)  # {ngram: {biz_id: count}}
    for biz_id, ngrams in biz_ngram_counts.items():
        for ng, cnt in ngrams.items():
            ngram_to_bizs[ng][biz_id] = cnt

    # Filter: phrases in min_restaurants-max_restaurants, sort by total mentions
    unique_phrases = []
    for ng, biz_counts in ngram_to_bizs.items():
        if min_restaurants <= len(biz_counts) <= max_restaurants:
            total_mentions = sum(biz_counts.values())
            unique_phrases.append((ng, len(biz_counts), total_mentions))

    # Sort by: fewest restaurants first, then most mentions
    unique_phrases.sort(key=lambda x: (x[1], -x[2]))

    return {
        'unique_phrases': {p[0]: {'restaurants': p[1], 'mentions': p[2]} for p in unique_phrases[:100]},
        'total_restaurants': len(biz_ngram_counts),
        'total_unique_phrases': len(unique_phrases)
    }


# Attribute keywords for review text analysis
ATTRIBUTE_KEYWORDS = {
    'noise': ['quiet', 'loud', 'noisy', 'peaceful', 'calm', 'deafening', 'silent'],
    'outdoor': ['outdoor', 'patio', 'sidewalk', 'rooftop', 'terrace', 'outside', 'garden'],
    'parking': ['parking', 'parked', 'garage', 'valet', 'street parking', 'lot'],
    'dietary': ['vegan', 'vegetarian', 'gluten', 'allergy', 'dairy-free', 'celiac', 'kosher', 'halal'],
    'kids': ['kids', 'children', 'family', 'stroller', 'highchair', 'kid-friendly'],
    'groups': ['group', 'party', 'large table', 'reservation', 'private room', 'event'],
    'wifi': ['wifi', 'wi-fi', 'internet', 'laptop', 'work', 'outlet', 'plug'],
    'wait': ['wait', 'waited', 'waiting', 'line', 'busy', 'crowded', 'packed'],
    'service': ['waiter', 'waitress', 'server', 'staff', 'manager', 'bartender', 'host'],
    'price': ['cheap', 'expensive', 'pricey', 'affordable', 'overpriced', 'worth', 'value'],
}


def analyze_per_restaurant(restaurants, reviews):
    """Per-restaurant statistics for selection."""
    # Build restaurant lookup
    biz_lookup = {r['business_id']: r.get('name', 'Unknown') for r in restaurants}

    # Group reviews by business
    reviews_by_biz = defaultdict(list)
    for r in reviews:
        reviews_by_biz[r['business_id']].append(r)

    per_restaurant = {}
    controversial = []  # High star variance
    review_rich = []    # Many reviews

    for bid, revs in reviews_by_biz.items():
        if bid not in biz_lookup:
            continue

        stars_list = [r.get('stars', 0) for r in revs if r.get('stars')]
        dates = [r.get('date', '') for r in revs if r.get('date')]
        lengths = [len(r.get('text', '')) for r in revs]
        elite_count = sum(1 for r in revs if r.get('user', {}).get('elite'))

        avg_stars = mean(stars_list) if stars_list else 0
        star_var = stdev(stars_list) if len(stars_list) > 1 else 0

        info = {
            'name': biz_lookup[bid],
            'review_count': len(revs),
            'avg_stars': round(avg_stars, 2),
            'star_variance': round(star_var, 2),
            'avg_length': round(mean(lengths)) if lengths else 0,
            'elite_ratio': round(elite_count / len(revs), 2) if revs else 0,
            'date_range': [min(dates), max(dates)] if dates else [],
            'recent_2020': sum(1 for d in dates if d >= '2020'),
        }
        per_restaurant[bid] = info

        # Track notable restaurants
        if star_var > 1.0:
            controversial.append((bid, star_var))
        if len(revs) >= 50:
            review_rich.append((bid, len(revs)))

    # Sort notable lists
    controversial.sort(key=lambda x: -x[1])
    review_rich.sort(key=lambda x: -x[1])

    return {
        'per_restaurant': per_restaurant,
        'controversial': [{'id': bid, 'name': biz_lookup.get(bid, '?'), 'variance': v} for bid, v in controversial[:20]],
        'review_rich': [{'id': bid, 'name': biz_lookup.get(bid, '?'), 'count': c} for bid, c in review_rich[:20]],
    }


def analyze_attribute_mentions(reviews):
    """Count attribute keyword mentions per restaurant."""
    reviews_by_biz = defaultdict(list)
    for r in reviews:
        reviews_by_biz[r['business_id']].append(r.get('text', '').lower())

    per_biz_mentions = {}
    global_counts = Counter()

    for bid, texts in reviews_by_biz.items():
        combined = ' '.join(texts)
        mentions = {}
        for attr, keywords in ATTRIBUTE_KEYWORDS.items():
            count = sum(combined.count(kw) for kw in keywords)
            if count > 0:
                mentions[attr] = count
                global_counts[attr] += count
        if mentions:
            per_biz_mentions[bid] = mentions

    return {
        'global_counts': dict(global_counts.most_common()),
        'per_restaurant': per_biz_mentions,
    }


def print_summary(rest_results, rev_results, text_results=None, per_rest_results=None, mention_results=None):
    """Print formatted summary to stdout."""
    n = rest_results['count']

    print(f"\n{'='*60}")
    print(f"RESTAURANT ANALYSIS ({n} restaurants)")
    print(f"{'='*60}")

    # Distributions
    dist = rest_results.get('distributions', {})

    print("\nNoise Level:")
    for level, count in sorted(dist.get('noise_level', {}).items(), key=lambda x: -x[1]):
        print(f"  {level}: {count}")

    print("\nOutdoor Seating:")
    for val, count in dist.get('outdoor_seating', {}).items():
        print(f"  {val}: {count}")

    print("\nPrice Range:")
    for pr, count in sorted(dist.get('price_range', {}).items()):
        print(f"  ${pr}: {count}")

    print("\nAmbience (True counts):")
    for amb, count in list(dist.get('ambience', {}).items())[:8]:
        print(f"  {amb}: {count}")

    print("\nParking (True counts):")
    for pk, count in dist.get('parking', {}).items():
        print(f"  {pk}: {count}")

    # Rare features
    print("\nRare Features (1-10 restaurants):")
    for attr, bids in rest_results.get('rare_features', {}).items():
        print(f"  {attr}: {len(bids)}")

    print("\nHours Patterns:")
    for k, v in rest_results.get('hours', {}).items():
        print(f"  {k}: {v}")

    # Reviews
    print(f"\n{'='*60}")
    print(f"REVIEW ANALYSIS ({rev_results['count']} reviews)")
    print(f"{'='*60}")

    elite_pct = rev_results['elite_count'] / rev_results['count'] * 100 if rev_results['count'] else 0
    print(f"\nElite reviews: {rev_results['elite_count']} ({elite_pct:.0f}%)")
    print(f"High-social users (100+ friends): {rev_results['high_social_count']}")

    if rev_results['date_range']:
        print(f"Date range: {rev_results['date_range'].get('earliest', 'N/A')} to {rev_results['date_range'].get('latest', 'N/A')}")
        print(f"Recent (2020+): {rev_results['date_range'].get('recent_2020', 0)}")

    eng = rev_results['engagement']
    print(f"\nEngagement: useful_avg={eng.get('useful_avg', 0)}, funny_avg={eng.get('funny_avg', 0)}")

    if rev_results['length_stats']:
        ls = rev_results['length_stats']
        print(f"Review Length: min={ls['min']}, max={ls['max']}, avg={ls['avg']}")

    # Per-restaurant stats
    if per_rest_results:
        print(f"\n{'='*60}")
        print(f"PER-RESTAURANT STATS")
        print(f"{'='*60}")

        print("\nControversial (high star variance):")
        for item in per_rest_results.get('controversial', [])[:10]:
            print(f"  {item['name'][:30]}: variance={item['variance']:.2f}")

        print("\nReview-Rich (50+ reviews):")
        for item in per_rest_results.get('review_rich', [])[:10]:
            print(f"  {item['name'][:30]}: {item['count']} reviews")

    # Attribute mentions
    if mention_results:
        print(f"\n{'='*60}")
        print(f"ATTRIBUTE MENTIONS IN REVIEWS")
        print(f"{'='*60}")
        print("\nGlobal keyword counts:")
        for attr, count in mention_results.get('global_counts', {}).items():
            print(f"  {attr}: {count}")

    # Text analysis
    if text_results:
        print(f"\n{'='*60}")
        print(f"SHARED PHRASES (3+ mentions, 3-5 restaurants)")
        print(f"{'='*60}")
        print(f"\nTotal: {text_results['total_unique_phrases']}")
        print("\nTop phrases:")
        for phrase, info in list(text_results['unique_phrases'].items())[:20]:
            print(f"  \"{phrase}\": {info['mentions']} mentions in {info['restaurants']} restaurant(s)")


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
    text_results = analyze_review_text(reviews)
    per_rest_results = analyze_per_restaurant(restaurants, reviews)
    mention_results = analyze_attribute_mentions(reviews)

    # Print summary
    print_summary(rest_results, rev_results, text_results, per_rest_results, mention_results)

    # Save full results as JSON
    output = {
        'summary': {
            'restaurant_count': rest_results['count'],
            'review_count': rev_results['count'],
            'date_range': rev_results.get('date_range', {}),
        },
        'distributions': rest_results.get('distributions', {}),
        'rare_features': rest_results.get('rare_features', {}),
        'categories': rest_results.get('categories', {}),
        'hours': rest_results.get('hours', {}),
        'reviews': rev_results,
        'per_restaurant': per_rest_results.get('per_restaurant', {}),
        'notable': {
            'controversial': per_rest_results.get('controversial', []),
            'review_rich': per_rest_results.get('review_rich', []),
        },
        'attribute_mentions': mention_results,
        'text_analysis': text_results,
    }
    out_path = selection_dir / 'analysis.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n\nFull results saved to {out_path}")


if __name__ == '__main__':
    main()
