#!/usr/bin/env python3
"""
Prototype: Single-restaurant rule-following task with contradictory reviews.

Test case:
- Question: "Is this restaurant good for a romantic dinner?"
- Rules define how to handle contradictions
- Ground truth is deterministic based on rules + data
"""

import json
import sys
from pathlib import Path

# Add parent to path for utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.llm import call_llm, configure

# Configure for reasoning models - they need high token budgets
configure(max_tokens_reasoning=32000)

DATA_FILE = Path(__file__).parent / "data" / "Acme_Oyster_House__ab50qdW.jsonl"


def load_restaurant_data(max_reviews: int = 100, recent_only: bool = True) -> tuple[dict, list[dict]]:
    """Load restaurant meta and subset of reviews.

    If recent_only=True, loads the LAST max_reviews (most recent).
    Otherwise loads first max_reviews (oldest).
    """
    with open(DATA_FILE) as f:
        meta = json.loads(f.readline())
        all_reviews = [json.loads(line) for line in f]

    if recent_only:
        # Take most recent reviews (data is sorted by date ascending)
        reviews = all_reviews[-max_reviews:]
    else:
        reviews = all_reviews[:max_reviews]

    print(f"Loaded {len(reviews)} reviews, date range: {reviews[0]['date'][:10]} to {reviews[-1]['date'][:10]}")
    return meta, reviews


def inject_synthetic_reviews(reviews: list[dict]) -> list[dict]:
    """
    Inject controlled reviews to create a deterministic test case.

    Scenario: "Is this good for a romantic dinner?"
    - Inject 2 positive reviews mentioning romantic/date (from 2021)
    - Inject 1 negative review mentioning romantic/date (from 2021)
    - Inject 1 review accusing the negative review of being fake (from 2021)

    With rule "discount reviews accused of being fake":
      -> Answer should be YES (2 positive, 0 negative after discount)

    Without that rule:
      -> Answer should be NO (2 positive, 1 negative = conflict)
    """

    # Clear any existing romantic-themed reviews to control the experiment
    reviews = [r for r in reviews if 'romantic' not in r['text'].lower()
               and 'date night' not in r['text'].lower()]

    # Inject controlled reviews
    injected = [
        {
            "_type": "review",
            "_injected": True,
            "review_id": "INJECT_POS_1",
            "stars": 5.0,
            "date": "2021-06-15 19:00:00",
            "text": "Perfect for a romantic dinner! The ambiance was wonderful, candlelit tables, and the chargrilled oysters were divine. My partner and I had an amazing anniversary here. Highly recommend for date night.",
            "useful": 12,
            "funny": 0,
            "cool": 5,
        },
        {
            "_type": "review",
            "_injected": True,
            "review_id": "INJECT_POS_2",
            "stars": 5.0,
            "date": "2021-08-22 20:30:00",
            "text": "Took my girlfriend here for our anniversary. The romantic atmosphere exceeded expectations. Service was attentive but not intrusive. The seafood was fresh and delicious. Will definitely return for special occasions.",
            "useful": 8,
            "funny": 0,
            "cool": 3,
        },
        {
            "_type": "review",
            "_injected": True,
            "review_id": "INJECT_NEG_1",
            "stars": 1.0,
            "date": "2021-07-10 21:00:00",
            "text": "Terrible for a romantic dinner. The noise level was unbearable - we couldn't hear each other talk. Tables are crammed together with no privacy. Food was mediocre at best. Ruined our date night completely. Avoid if you want any kind of intimate atmosphere.",
            "useful": 15,
            "funny": 2,
            "cool": 0,
        },
        {
            "_type": "review",
            "_injected": True,
            "review_id": "INJECT_META_1",
            "stars": 4.0,
            "date": "2021-09-05 18:00:00",
            "text": "Great oysters as always. I noticed a very negative review from July 2021 claiming this place is 'terrible for romantic dinner' - that review seems fake or exaggerated. I've been here multiple times for date nights and it's always been lovely. Don't trust that one-star review about romantic atmosphere, it doesn't match reality at all.",
            "useful": 20,
            "funny": 1,
            "cool": 8,
        },
    ]

    return reviews + injected


def create_test_case(meta: dict, reviews: list[dict], rule_variant: str = "with_discount") -> dict:
    """
    Create a complete test case with question and rules.

    rule_variant:
      - "with_discount": Include rule to discount accused-fake reviews -> Answer: YES
      - "without_discount": No discount rule -> Answer: NO (conflict exists)
      - "strict_negative": Any negative = No -> Answer: NO
    """

    # Base rules
    rules = [
        "Only consider reviews from 2021 or later.",
        "Only consider reviews that specifically mention 'romantic', 'date', 'anniversary', or 'intimate'.",
    ]

    # Variant-specific rules
    if rule_variant == "with_discount":
        rules.append("If a review accuses another specific review of being fake or exaggerated, discount (ignore) the accused review.")
        rules.append("After applying all filters, if remaining relevant reviews are all positive (4+ stars), answer YES. If any negative reviews remain, answer NO.")
        expected_answer = "YES"
        reasoning = "After filtering to 2021+ romantic reviews: 2 positive, 1 negative. The negative review is accused of being fake by another review, so it's discounted. Remaining: 2 positive. Answer: YES."

    elif rule_variant == "without_discount":
        rules.append("After applying all filters, if remaining relevant reviews are all positive (4+ stars), answer YES. If any negative reviews remain, answer NO.")
        expected_answer = "NO"
        reasoning = "After filtering to 2021+ romantic reviews: 2 positive, 1 negative. Conflict exists. Answer: NO."

    elif rule_variant == "strict_negative":
        rules.append("If ANY relevant review is negative (1-2 stars), regardless of other reviews, answer NO.")
        expected_answer = "NO"
        reasoning = "There exists a 1-star review mentioning romantic dinner. Strict rule: any negative = NO."

    else:
        raise ValueError(f"Unknown rule variant: {rule_variant}")

    return {
        "restaurant": {
            "name": meta["name"],
            "stars": meta["stars"],
            "review_count": meta["review_count"],
            "categories": meta["categories"],
        },
        "reviews": reviews,
        "query": {
            "question": "Is this restaurant good for a romantic dinner?",
            "rules": rules,
            "answer_format": "Answer YES or NO, followed by your reasoning.",
        },
        "_ground_truth": {
            "expected_answer": expected_answer,
            "reasoning": reasoning,
            "rule_variant": rule_variant,
        }
    }


def build_prompt(test_case: dict) -> str:
    """Build the LLM prompt from test case."""

    # Format reviews
    reviews_text = []
    for i, r in enumerate(test_case["reviews"], 1):
        reviews_text.append(
            f"[Review {i}] Date: {r['date'][:10]} | Stars: {r['stars']}/5 | Useful votes: {r.get('useful', 0)}\n"
            f"{r['text']}\n"
        )

    prompt = f"""You are evaluating a restaurant based on its reviews. You must follow the rules exactly.

## Restaurant
Name: {test_case["restaurant"]["name"]}
Overall Rating: {test_case["restaurant"]["stars"]}/5
Categories: {test_case["restaurant"]["categories"]}

## Reviews
{chr(10).join(reviews_text)}

## Question
{test_case["query"]["question"]}

## Rules (YOU MUST FOLLOW THESE EXACTLY)
{chr(10).join(f"{i+1}. {rule}" for i, rule in enumerate(test_case["query"]["rules"]))}

## Instructions
{test_case["query"]["answer_format"]}

Think step by step:
1. First, identify which reviews pass the date filter
2. Then, identify which of those mention the relevant topics
3. Apply any discount/exclusion rules
4. Count remaining positive vs negative reviews
5. Apply the final decision rule

Your answer:"""

    return prompt


def run_test(rule_variant: str = "with_discount", max_reviews: int = 50):
    """Run a single test case."""

    print(f"\n{'='*60}")
    print(f"TEST CASE: {rule_variant}")
    print('='*60)

    # Load and prepare data
    meta, reviews = load_restaurant_data(max_reviews)
    reviews = inject_synthetic_reviews(reviews)

    # Create test case
    test_case = create_test_case(meta, reviews, rule_variant)

    print(f"\nQuestion: {test_case['query']['question']}")
    print(f"\nRules:")
    for i, rule in enumerate(test_case['query']['rules'], 1):
        print(f"  {i}. {rule}")
    print(f"\nExpected answer: {test_case['_ground_truth']['expected_answer']}")
    print(f"Reasoning: {test_case['_ground_truth']['reasoning']}")

    # Build prompt
    prompt = build_prompt(test_case)

    print(f"\n--- Prompt length: {len(prompt)} chars ---")

    # Call LLM
    print("\nCalling LLM...")
    response = call_llm(prompt)

    print(f"\n--- LLM Response ---")
    print(response)

    # Check if answer matches
    expected = test_case['_ground_truth']['expected_answer']
    # Simple check: does response start with or contain the expected answer
    response_upper = response.upper()
    if expected in response_upper[:50]:  # Check beginning of response
        print(f"\n✓ PASS: LLM answered {expected} as expected")
        return True
    else:
        print(f"\n✗ FAIL: Expected {expected}, but got different answer")
        return False


def main():
    """Run all test variants."""

    print("Prototype: Rule-Following with Contradictory Reviews")
    print("="*60)

    results = {}

    # Test all variants
    for variant in ["with_discount", "without_discount", "strict_negative"]:
        try:
            passed = run_test(variant)
            results[variant] = "PASS" if passed else "FAIL"
        except Exception as e:
            print(f"\nERROR in {variant}: {e}")
            results[variant] = f"ERROR: {e}"

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for variant, result in results.items():
        print(f"  {variant}: {result}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["with_discount", "without_discount", "strict_negative", "all"],
                        default="all", help="Which rule variant to test")
    parser.add_argument("--max-reviews", type=int, default=50, help="Max reviews to include")
    args = parser.parse_args()

    if args.variant == "all":
        main()
    else:
        run_test(args.variant, args.max_reviews)
