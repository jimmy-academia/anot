#!/usr/bin/env python3
"""
Extract restaurants with highest review counts from raw Yelp data.
Creates individual JSONL files per restaurant in explore/data/
"""

import json
import os
from pathlib import Path
from collections import defaultdict

RAW_DIR = Path(__file__).parent.parent / "preprocessing" / "raw"
OUT_DIR = Path(__file__).parent / "data"

BUSINESS_FILE = RAW_DIR / "yelp_academic_dataset_business.json"
REVIEW_FILE = RAW_DIR / "yelp_academic_dataset_review.json"

# Config
TOP_N = 10  # Number of restaurants to extract
MIN_REVIEWS = 200  # Minimum review count to consider


def find_top_restaurants(n: int = TOP_N) -> list[dict]:
    """Find top N restaurants by review count."""
    print(f"Scanning businesses for top {n} restaurants...")

    candidates = []
    with open(BUSINESS_FILE) as f:
        for line in f:
            biz = json.loads(line)

            # Filter: must be a restaurant/cafe/food place
            categories = biz.get("categories") or ""
            if not any(cat in categories for cat in ["Restaurant", "Cafe", "Food", "Coffee"]):
                continue

            # Filter: minimum review count
            if biz.get("review_count", 0) < MIN_REVIEWS:
                continue

            candidates.append({
                "business_id": biz["business_id"],
                "name": biz["name"],
                "review_count": biz["review_count"],
                "stars": biz["stars"],
                "categories": categories,
                "city": biz.get("city", ""),
                "state": biz.get("state", ""),
                "attributes": biz.get("attributes", {}),
            })

    # Sort by review count descending
    candidates.sort(key=lambda x: x["review_count"], reverse=True)

    print(f"Found {len(candidates)} restaurants with {MIN_REVIEWS}+ reviews")
    for i, biz in enumerate(candidates[:n]):
        print(f"  {i+1}. {biz['name'][:50]} - {biz['review_count']} reviews ({biz['city']}, {biz['state']})")

    return candidates[:n]


def extract_reviews(business_ids: set[str]) -> dict[str, list[dict]]:
    """Extract all reviews for given business IDs."""
    print(f"\nExtracting reviews for {len(business_ids)} businesses...")
    print("(This may take a few minutes for the 5GB review file)")

    reviews_by_biz = defaultdict(list)
    total = 0

    with open(REVIEW_FILE) as f:
        for i, line in enumerate(f):
            if i % 1_000_000 == 0 and i > 0:
                print(f"  Processed {i:,} reviews, found {total:,} matches...")

            review = json.loads(line)
            biz_id = review["business_id"]

            if biz_id in business_ids:
                reviews_by_biz[biz_id].append(review)
                total += 1

    print(f"  Done! Extracted {total:,} reviews total")
    return reviews_by_biz


def save_datasets(restaurants: list[dict], reviews_by_biz: dict[str, list[dict]]):
    """Save each restaurant as a separate JSONL file."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save index file
    index = []
    for biz in restaurants:
        biz_id = biz["business_id"]
        reviews = reviews_by_biz.get(biz_id, [])

        # Sort reviews by date
        reviews.sort(key=lambda r: r["date"])

        # Create safe filename
        safe_name = "".join(c if c.isalnum() else "_" for c in biz["name"][:30])
        filename = f"{safe_name}_{biz_id[:8]}.jsonl"
        filepath = OUT_DIR / filename

        # Write restaurant meta + reviews
        with open(filepath, "w") as f:
            # First line is restaurant metadata
            f.write(json.dumps({"_type": "meta", **biz}) + "\n")
            # Remaining lines are reviews
            for review in reviews:
                f.write(json.dumps({"_type": "review", **review}) + "\n")

        index.append({
            "filename": filename,
            "name": biz["name"],
            "review_count": len(reviews),
            "stars": biz["stars"],
            "city": biz["city"],
        })
        print(f"  Saved {filename} ({len(reviews)} reviews)")

    # Save index
    with open(OUT_DIR / "index.json", "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nSaved {len(index)} datasets to {OUT_DIR}/")


def main():
    # Step 1: Find top restaurants
    restaurants = find_top_restaurants(TOP_N)

    if not restaurants:
        print("No restaurants found matching criteria!")
        return

    # Step 2: Extract their reviews
    business_ids = {r["business_id"] for r in restaurants}
    reviews_by_biz = extract_reviews(business_ids)

    # Step 3: Save
    save_datasets(restaurants, reviews_by_biz)


if __name__ == "__main__":
    main()
