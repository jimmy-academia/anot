#!/usr/bin/env python3
"""Validate review_sentiment evidence using LLM with caching.

Checks if gold restaurants truly have positive sentiment for specified topics.
Uses cached judgments to avoid redundant LLM calls.
"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict

# Cache file path
CACHE_PATH = Path(__file__).parent.parent / 'philly_cafes' / 'judgement_cache.json'


def load_cache() -> dict:
    """Load existing judgement cache."""
    if CACHE_PATH.exists():
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    """Save judgement cache."""
    with open(CACHE_PATH, 'w') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def get_sentiment_heuristic(reviews: list, topic: str) -> tuple:
    """Count positive (4-5★) and negative (1-2★) reviews mentioning topic.

    Returns (positive_count, negative_count, matching_reviews).
    """
    pattern = re.escape(topic)
    pos, neg = 0, 0
    matching = []

    for r in reviews:
        text = r.get('text', '')
        if re.search(pattern, text, re.IGNORECASE):
            stars = r.get('stars', 3)
            if stars >= 4:
                pos += 1
                matching.append({'stars': stars, 'sentiment': 'positive', 'snippet': text[:200]})
            elif stars <= 2:
                neg += 1
                matching.append({'stars': stars, 'sentiment': 'negative', 'snippet': text[:200]})

    return pos, neg, matching[:5]


def llm_judge_sentiment(reviews: list, topic: str, business_name: str) -> dict:
    """Use LLM to judge if reviews are positive about topic.

    This is called only when heuristic is ambiguous or for verification.
    """
    # Import LLM utilities lazily to avoid circular imports
    from utils.llm import call_llm

    # Collect reviews mentioning the topic
    pattern = re.escape(topic)
    relevant = []
    for r in reviews:
        text = r.get('text', '')
        if re.search(pattern, text, re.IGNORECASE):
            relevant.append({'stars': r.get('stars', 3), 'text': text[:500]})

    if not relevant:
        return {'sentiment': 'none', 'confidence': 1.0, 'reason': 'No reviews mention topic'}

    # Build prompt
    reviews_text = '\n'.join([
        f"[{r['stars']}★] {r['text']}" for r in relevant[:10]
    ])

    prompt = f"""Analyze reviews for "{business_name}" about "{topic}".

REVIEWS:
{reviews_text}

QUESTION: Are these reviews POSITIVE about "{topic}"?
- "positive": reviewers praise/recommend this aspect
- "negative": reviewers complain/criticize this aspect
- "mixed": both positive and negative opinions
- "neutral": mentions without clear sentiment

OUTPUT JSON:
{{"sentiment": "positive/negative/mixed/neutral", "confidence": 0.0-1.0, "reason": "brief explanation"}}"""

    response = call_llm(prompt, max_tokens=256)

    # Parse response
    try:
        # Extract JSON from response
        match = re.search(r'\{[^}]+\}', response)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass

    # Fallback to heuristic
    pos, neg, _ = get_sentiment_heuristic(reviews, topic)
    return {
        'sentiment': 'positive' if pos > neg else ('negative' if neg > pos else 'neutral'),
        'confidence': 0.5,
        'reason': 'LLM parse failed, used heuristic'
    }


def validate_request(request: dict, reviews_by_biz: dict, restaurants: dict, cache: dict, use_llm: bool = False) -> dict:
    """Validate a single request's review_sentiment evidence.

    Returns validation result dict.
    """
    req_id = request.get('id', 'unknown')
    gold_biz = request.get('gold_restaurant')

    # Find review_sentiment evidence
    evidence = None
    for arg in request.get('structure', {}).get('args', []):
        ev = arg.get('evidence', {})
        if ev.get('kind') == 'review_sentiment':
            evidence = ev
            break

    if not evidence:
        return {'request_id': req_id, 'status': 'skip', 'reason': 'No review_sentiment evidence'}

    topic = evidence.get('topic', '')
    expected_sentiment = evidence.get('sentiment', 'positive')

    # Cache key
    cache_key = f"{gold_biz}:{topic}"

    # Check cache first
    if cache_key in cache:
        cached = cache[cache_key]
        is_valid = cached.get('is_valid_positive', False)
        return {
            'request_id': req_id,
            'status': 'valid' if is_valid else 'invalid',
            'source': 'cache',
            'positive': cached.get('positive_count', 0),
            'negative': cached.get('negative_count', 0),
            'topic': topic,
            'business': cached.get('business_name', gold_biz[:12])
        }

    # Not in cache - compute
    reviews = reviews_by_biz.get(gold_biz, [])
    business_name = restaurants.get(gold_biz, {}).get('name', gold_biz[:12])

    if use_llm:
        result = llm_judge_sentiment(reviews, topic, business_name)
        is_positive = result['sentiment'] == 'positive'
    else:
        pos, neg, samples = get_sentiment_heuristic(reviews, topic)
        is_positive = pos >= 1 and pos > neg
        result = {'positive_count': pos, 'negative_count': neg}

    # Update cache
    cache[cache_key] = {
        'business_id': gold_biz,
        'business_name': business_name,
        'topic': topic,
        'positive_count': result.get('positive_count', 0),
        'negative_count': result.get('negative_count', 0),
        'sentiment': 'positive' if is_positive else 'negative',
        'is_valid_positive': is_positive,
        'llm_result': result if use_llm else None
    }

    return {
        'request_id': req_id,
        'status': 'valid' if is_positive else 'invalid',
        'source': 'computed',
        'positive': result.get('positive_count', 0),
        'negative': result.get('negative_count', 0),
        'topic': topic,
        'business': business_name
    }


def main():
    """Validate all review_sentiment requests."""
    import argparse
    parser = argparse.ArgumentParser(description='Validate review_sentiment evidence')
    parser.add_argument('--use-llm', action='store_true', help='Use LLM for ambiguous cases')
    parser.add_argument('--recompute', action='store_true', help='Ignore cache, recompute all')
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / 'philly_cafes'

    # Load data
    reviews_by_biz = defaultdict(list)
    with open(data_dir / 'reviews.jsonl') as f:
        for line in f:
            r = json.loads(line)
            reviews_by_biz[r['business_id']].append(r)

    restaurants = {}
    with open(data_dir / 'restaurants.jsonl') as f:
        for line in f:
            r = json.loads(line)
            restaurants[r['business_id']] = r

    # Load cache (or empty if recompute)
    cache = {} if args.recompute else load_cache()

    # Validate each request
    results = []
    with open(data_dir / 'requests.jsonl') as f:
        for line in f:
            req = json.loads(line)
            result = validate_request(req, reviews_by_biz, restaurants, cache, use_llm=args.use_llm)
            if result['status'] != 'skip':
                results.append(result)
                status_icon = '✓' if result['status'] == 'valid' else '✗'
                print(f"{status_icon} {result['request_id']}: {result['business'][:20]:20s} | {result['topic']:15s} | +{result['positive']}/-{result['negative']} [{result['source']}]")

    # Save updated cache
    save_cache(cache)

    # Summary
    valid = sum(1 for r in results if r['status'] == 'valid')
    invalid = sum(1 for r in results if r['status'] == 'invalid')
    print(f"\nSummary: {valid} valid, {invalid} invalid out of {len(results)} review_sentiment requests")
    print(f"Cache saved to {CACHE_PATH}")


if __name__ == '__main__':
    main()
