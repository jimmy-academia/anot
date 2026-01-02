#!/usr/bin/env python3
"""Curate Yelp restaurants with LLM-assisted category validation.

Usage:
    python preprocessing/scripts/curate.py --name philly_cafes --city Philadelphia --category "Coffee & Tea" Cafes
    python preprocessing/scripts/curate.py --name philly_bars --city Philadelphia --category Bars Nightlife --skip-llm

Output:
    preprocessing/output/{name}/
    ├── restaurants.jsonl   # Restaurant metadata
    ├── reviews.jsonl       # ALL reviews with user data
    └── meta.json           # Creation params + stats
"""

import argparse
import asyncio
import json
import random
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path for utils import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils.llm import call_llm, call_llm_async

# File paths
RAW_DIR = Path("preprocessing/raw")
OUTPUT_DIR = Path("preprocessing/output")
BUSINESS_FILE = RAW_DIR / "yelp_academic_dataset_business.json"
REVIEW_FILE = RAW_DIR / "yelp_academic_dataset_review.json"
USER_FILE = RAW_DIR / "yelp_academic_dataset_user.json"


class Curator:
    """Curate restaurants from Yelp data."""

    def __init__(self, name: str, city: str, categories: List[str],
                 target: int = 100, threshold: int = 70, batch_size: int = 20,
                 skip_llm: bool = False):
        self.name = name
        self.city = city
        self.categories = categories
        self.output_dir = OUTPUT_DIR / name

        self.target = target
        self.threshold = threshold
        self.batch_size = batch_size
        self.skip_llm = skip_llm

        self.businesses: Dict[str, dict] = {}
        self.reviews_by_biz: Dict[str, List[dict]] = defaultdict(list)
        self.users: Dict[str, dict] = {}
        self.category_keywords: List[str] = []
        self.scored_results: List[Tuple[dict, int, str]] = []

    def load_business_data(self) -> None:
        """Load restaurant businesses from Yelp data."""
        print(f"Loading business data from {BUSINESS_FILE}...")
        with open(BUSINESS_FILE) as f:
            for line in f:
                biz = json.loads(line)
                cats = biz.get("categories", "") or ""
                if "Restaurant" in cats or "Bars" in cats or "Nightlife" in cats or "Cafes" in cats or "Coffee" in cats:
                    self.businesses[biz["business_id"]] = biz
        print(f"Loaded {len(self.businesses)} restaurants/bars/cafes")

    def get_filtered_businesses(self) -> List[dict]:
        """Get businesses matching city and categories."""
        results = []
        for biz in self.businesses.values():
            if biz.get("city") != self.city:
                continue
            cats = biz.get("categories", "") or ""
            if any(cat in cats for cat in self.categories):
                results.append(biz)
        return results

    def load_reviews(self, business_ids: set) -> None:
        """Load reviews for specified businesses."""
        print(f"Loading reviews for {len(business_ids)} businesses...")
        self.reviews_by_biz.clear()
        count = 0
        with open(REVIEW_FILE) as f:
            for i, line in enumerate(f):
                if i % 1000000 == 0 and i > 0:
                    print(f"  Processed {i:,} reviews...")
                review = json.loads(line)
                bid = review["business_id"]
                if bid in business_ids:
                    self.reviews_by_biz[bid].append(review)
                    count += 1
        print(f"Loaded {count:,} reviews")

    def load_users(self, user_ids: set) -> None:
        """Load user data for review authors."""
        print(f"Loading user data for {len(user_ids)} users...")
        with open(USER_FILE) as f:
            for line in f:
                user = json.loads(line)
                if user["user_id"] in user_ids:
                    self.users[user["user_id"]] = user
        print(f"Loaded {len(self.users)} users")

    def compute_richness_scores(self) -> List[Tuple[dict, int]]:
        """Compute richness (total review char count) for filtered businesses."""
        scored = []
        for biz in self.get_filtered_businesses():
            bid = biz["business_id"]
            reviews = self.reviews_by_biz.get(bid, [])
            richness = sum(len(r.get("text", "")) for r in reviews)
            scored.append((biz, richness))
        return sorted(scored, key=lambda x: -x[1])

    def generate_category_keywords(self) -> List[str]:
        """Use LLM to generate keywords for the categories."""
        cats = ", ".join(self.categories)
        prompt = f"""For the category "{cats}", list keywords that would appear in reviews if the business truly belongs to this category.

Return ONLY a comma-separated list of 10-15 lowercase keywords."""

        try:
            response = call_llm(prompt, system="You are a cuisine expert.")
            keywords = [kw.strip().lower() for kw in response.split(",") if kw.strip()]
            keywords.extend([cat.lower() for cat in self.categories])
            return list(set(keywords))
        except Exception:
            return [cat.lower() for cat in self.categories]

    def get_keyword_evidence(self, biz: dict, max_snippets: int = 5) -> Tuple[List[str], int, int]:
        """Find review snippets containing keywords."""
        reviews = self.reviews_by_biz.get(biz["business_id"], [])
        total = len(reviews)
        matches = []

        for r in reviews:
            text = r.get("text", "")
            text_lower = text.lower()
            for kw in self.category_keywords:
                if kw in text_lower:
                    idx = text_lower.find(kw)
                    start = max(0, idx - 100)
                    end = min(len(text), idx + 300)
                    snippet = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
                    matches.append(snippet)
                    break

        return matches[:max_snippets], len(matches), total

    def parse_percentage(self, response: str) -> int:
        """Extract percentage from LLM response."""
        match = re.search(r'(\d+)%', response)
        return int(match.group(1)) if match else 0

    async def estimate_category_fit_async(self, biz: dict) -> Tuple[dict, int, str]:
        """Async LLM category estimation."""
        reviews = self.reviews_by_biz.get(biz["business_id"], [])
        total_reviews = len(reviews)

        evidence_snippets, evidence_count, _ = self.get_keyword_evidence(biz, max_snippets=5)
        evidence_texts = "\n---\n".join(evidence_snippets) if evidence_snippets else "(None)"

        sample_reviews = reviews[:10]
        review_texts = "\n---\n".join([r.get("text", "")[:500] for r in sample_reviews])

        cats = ", ".join(self.categories)
        prompt = f"""Estimate probability (0-100%) this business belongs to "{cats}".

Business: {biz.get('name')}
Listed categories: {biz.get('categories', 'Unknown')}
Keyword matches: {evidence_count} / {total_reviews} reviews

=== Evidence ===
{evidence_texts}

=== Sample reviews ===
{review_texts}

Reply: "XX% - reason"
"""

        try:
            response = await call_llm_async(prompt, system="You are a data quality evaluator.")
            pct = self.parse_percentage(response.strip())
            return (biz, pct, response.strip())
        except Exception as e:
            return (biz, 0, f"[Error: {e}]")

    def estimate_simple(self, biz: dict) -> Tuple[dict, int, str]:
        """Simple heuristic scoring without LLM."""
        reviews = self.reviews_by_biz.get(biz["business_id"], [])
        total_reviews = len(reviews)

        if total_reviews == 0:
            return (biz, 0, "No reviews")

        _, match_count, _ = self.get_keyword_evidence(biz)
        match_ratio = match_count / total_reviews if total_reviews > 0 else 0
        stars = biz.get("stars", 3)
        review_bonus = min(20, total_reviews // 10)

        pct = int(match_ratio * 60 + stars * 5 + review_bonus)
        pct = min(100, max(0, pct))

        reason = f"{pct}% - {match_count}/{total_reviews} keyword matches, {stars}★"
        return (biz, pct, reason)

    async def score_businesses(self) -> None:
        """Score businesses by category fit."""
        scored = self.compute_richness_scores()
        print(f"\nScoring {len(scored)} businesses...")

        all_results = []
        above_threshold = 0

        for batch_start in range(0, len(scored), self.batch_size):
            batch = scored[batch_start:batch_start + self.batch_size]
            print(f"Batch {batch_start//self.batch_size + 1} ({batch_start+1}-{batch_start+len(batch)})...")

            if self.skip_llm:
                results = [self.estimate_simple(biz) for biz, _ in batch]
            else:
                tasks = [self.estimate_category_fit_async(biz) for biz, _ in batch]
                results = await asyncio.gather(*tasks)

            all_results.extend(results)
            above_threshold = sum(1 for _, pct, _ in all_results if pct >= self.threshold)

            if above_threshold >= self.target:
                print(f"Reached {self.target} above {self.threshold}%. Stopping.")
                break

        all_results.sort(key=lambda x: -x[1])
        self.scored_results = all_results

        print(f"\nScored {len(all_results)} businesses")
        print(f"Above {self.threshold}%: {above_threshold}")

    def write_output(self) -> None:
        """Write restaurants.jsonl, reviews.jsonl, and meta.json."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Get top businesses above threshold (or all if fewer)
        selected = [(biz, pct, reason) for biz, pct, reason in self.scored_results if pct >= self.threshold]
        if len(selected) < self.target:
            selected = self.scored_results[:self.target]

        selected_ids = {biz["business_id"] for biz, _, _ in selected}

        # Collect user_ids for selected businesses
        user_ids = set()
        for bid in selected_ids:
            for r in self.reviews_by_biz.get(bid, []):
                user_ids.add(r["user_id"])

        # Load user data
        self.load_users(user_ids)

        # Write restaurants.jsonl
        restaurants_file = self.output_dir / "restaurants.jsonl"
        with open(restaurants_file, "w") as f:
            for biz, pct, reason in selected:
                record = {
                    "business_id": biz["business_id"],
                    "name": biz.get("name", ""),
                    "address": biz.get("address", ""),
                    "city": biz.get("city", ""),
                    "state": biz.get("state", ""),
                    "postal_code": biz.get("postal_code", ""),
                    "latitude": biz.get("latitude"),
                    "longitude": biz.get("longitude"),
                    "stars": biz.get("stars"),
                    "review_count": biz.get("review_count"),
                    "is_open": biz.get("is_open"),
                    "attributes": biz.get("attributes", {}),
                    "categories": biz.get("categories", ""),
                    "hours": biz.get("hours"),
                    "llm_score": pct,
                    "llm_reasoning": reason
                }
                f.write(json.dumps(record) + "\n")
        print(f"Wrote {len(selected)} restaurants to {restaurants_file}")

        # Write reviews.jsonl
        reviews_file = self.output_dir / "reviews.jsonl"
        review_count = 0
        with open(reviews_file, "w") as f:
            for bid in selected_ids:
                for r in self.reviews_by_biz.get(bid, []):
                    user = self.users.get(r["user_id"], {})
                    record = {
                        "review_id": r["review_id"],
                        "business_id": r["business_id"],
                        "user_id": r["user_id"],
                        "stars": r.get("stars"),
                        "date": r.get("date", ""),
                        "text": r.get("text", ""),
                        "useful": r.get("useful", 0),
                        "funny": r.get("funny", 0),
                        "cool": r.get("cool", 0),
                        "user": {
                            "name": user.get("name", ""),
                            "review_count": user.get("review_count", 0),
                            "yelping_since": user.get("yelping_since", ""),
                            "friends": user.get("friends", ""),
                            "elite": user.get("elite", ""),
                            "average_stars": user.get("average_stars"),
                            "fans": user.get("fans", 0)
                        }
                    }
                    f.write(json.dumps(record) + "\n")
                    review_count += 1
        print(f"Wrote {review_count} reviews to {reviews_file}")

        # Write meta.json
        meta_file = self.output_dir / "meta.json"
        meta = {
            "name": self.name,
            "city": self.city,
            "categories": self.categories,
            "created": datetime.now().isoformat(),
            "params": {
                "target": self.target,
                "threshold": self.threshold,
                "skip_llm": self.skip_llm
            },
            "stats": {
                "restaurants": len(selected),
                "reviews": review_count
            }
        }
        with open(meta_file, "w") as f:
            json.dump(meta, f, indent=2)
        print(f"Wrote metadata to {meta_file}")

    def run(self) -> None:
        """Main entry point."""
        print(f"{'=' * 60}")
        print(f"Curating: {self.city} > {', '.join(self.categories)}")
        print(f"Output: {self.output_dir}")
        print(f"{'=' * 60}")

        self.load_business_data()

        filtered = self.get_filtered_businesses()
        print(f"Found {len(filtered)} matching businesses")

        if not filtered:
            print("No businesses found. Exiting.")
            return

        business_ids = {b["business_id"] for b in filtered}
        self.load_reviews(business_ids)

        if not self.skip_llm:
            print("Generating category keywords...")
            self.category_keywords = self.generate_category_keywords()
            print(f"Keywords: {', '.join(self.category_keywords[:10])}...")
        else:
            self.category_keywords = [cat.lower() for cat in self.categories]

        asyncio.run(self.score_businesses())

        self.write_output()

        print(f"\n{'=' * 60}")
        print(f"Complete! Output: {self.output_dir}")
        print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Curate Yelp restaurants")
    parser.add_argument("--name", required=True, help="Selection name (e.g., philly_cafes)")
    parser.add_argument("--city", required=True, help="City name (e.g., Philadelphia)")
    parser.add_argument("--category", required=True, nargs="+", help="Categories (e.g., Cafes 'Coffee & Tea')")
    parser.add_argument("--target", type=int, default=100, help="Target number of restaurants")
    parser.add_argument("--threshold", type=int, default=70, help="Minimum LLM score threshold")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size for async")
    parser.add_argument("--skip-llm", action="store_true", help="Use heuristic instead of LLM")

    args = parser.parse_args()

    curator = Curator(
        name=args.name,
        city=args.city,
        categories=args.category,
        target=args.target,
        threshold=args.threshold,
        batch_size=args.batch_size,
        skip_llm=args.skip_llm
    )
    curator.run()


if __name__ == "__main__":
    main()
