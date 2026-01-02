#!/usr/bin/env python3
"""Yelp data curation with interactive selection and LLM-assisted scoring.

Usage:
    # Interactive mode (default)
    python -m preprocessing.curate

    # Non-interactive with CLI args
    python -m preprocessing.curate --name philly_cafes --city Philadelphia --category Bars --skip-llm
"""

import argparse
import asyncio
import json
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from utils.llm import call_llm, call_llm_async

# File paths
RAW_DIR = Path("preprocessing/raw")
OUTPUT_DIR = Path("preprocessing/output")
BUSINESS_FILE = RAW_DIR / "yelp_academic_dataset_business.json"
REVIEW_FILE = RAW_DIR / "yelp_academic_dataset_review.json"
USER_FILE = RAW_DIR / "yelp_academic_dataset_user.json"

console = Console()


class Curator:
    """Interactive Yelp data curation tool."""

    def __init__(self, name: str = None, city: str = None, categories: List[str] = None,
                 target: int = 100, threshold: int = 70, batch_size: int = 20,
                 skip_llm: bool = False):
        self.name = name
        self.city = city
        self.categories = categories or []
        self.output_dir = OUTPUT_DIR / name if name else None

        self.target = target
        self.threshold = threshold
        self.batch_size = batch_size
        self.skip_llm = skip_llm

        self.businesses: Dict[str, dict] = {}
        self.reviews_by_biz: Dict[str, List[dict]] = defaultdict(list)
        self.users: Dict[str, dict] = {}
        self.category_keywords: List[str] = []
        self.scored_results: List[Tuple[dict, int, str]] = []

    # ─────────────────────────────────────────────────────────────────────────
    # Data Loading
    # ─────────────────────────────────────────────────────────────────────────

    def load_business_data(self) -> None:
        """Load restaurant businesses from Yelp data."""
        if not BUSINESS_FILE.exists():
            console.print(f"[red]Error: Business file not found: {BUSINESS_FILE}[/red]")
            console.print("Please place Yelp academic dataset files in preprocessing/raw/")
            sys.exit(1)

        with console.status("[bold green]Loading business data..."):
            with open(BUSINESS_FILE) as f:
                for line in f:
                    biz = json.loads(line)
                    cats = biz.get("categories", "") or ""
                    if "Restaurant" in cats or "Bars" in cats or "Nightlife" in cats or "Cafes" in cats or "Coffee" in cats:
                        self.businesses[biz["business_id"]] = biz
        console.print(f"[green]Loaded {len(self.businesses):,} restaurants/bars/cafes[/green]")

    def load_reviews(self, business_ids: set) -> None:
        """Load reviews for specified businesses."""
        self.reviews_by_biz.clear()
        count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Loading reviews for {len(business_ids)} businesses...", total=None)
            with open(REVIEW_FILE) as f:
                for i, line in enumerate(f):
                    if i % 500000 == 0 and i > 0:
                        progress.update(task, description=f"Processing reviews... ({i:,} scanned)")
                    review = json.loads(line)
                    bid = review["business_id"]
                    if bid in business_ids:
                        self.reviews_by_biz[bid].append(review)
                        count += 1
            progress.update(task, completed=True)
        console.print(f"[green]Loaded {count:,} reviews[/green]")

    def load_users(self, user_ids: set) -> None:
        """Load user data for review authors."""
        with console.status(f"[bold green]Loading user data for {len(user_ids):,} users..."):
            with open(USER_FILE) as f:
                for line in f:
                    user = json.loads(line)
                    if user["user_id"] in user_ids:
                        self.users[user["user_id"]] = user
        console.print(f"[green]Loaded {len(self.users):,} users[/green]")

    # ─────────────────────────────────────────────────────────────────────────
    # Interactive Selection
    # ─────────────────────────────────────────────────────────────────────────

    def get_city_counts(self) -> Dict[str, int]:
        """Count restaurants per city."""
        counts = Counter(biz.get("city") for biz in self.businesses.values() if biz.get("city"))
        return dict(counts.most_common())

    def get_category_counts(self, city: str) -> Dict[str, int]:
        """Count categories within a city."""
        counts = Counter()
        for biz in self.businesses.values():
            if biz.get("city") != city:
                continue
            cats = biz.get("categories", "") or ""
            for cat in cats.split(","):
                cat = cat.strip()
                if cat and cat != "Restaurants":
                    counts[cat] += 1
        return dict(counts.most_common())

    def search_items(self, query: str, items: list) -> list:
        """Search items by name (case-insensitive partial match)."""
        query_lower = query.lower()
        return [(name, count) for name, count in items if query_lower in name.lower()]

    def paginated_select(self, items: list, title: str, prompt_text: str,
                         page_size: int = 20, allow_back: bool = False) -> tuple:
        """Reusable paginated selection with search.

        Returns: (action, selection, page)
        Actions: 'select', 'back', 'quit', or None (continue loop)
        """
        page = 0
        total_pages = max(1, (len(items) + page_size - 1) // page_size)

        while True:
            start = page * page_size
            end = min(start + page_size, len(items))
            displayed = items[start:end]

            table = Table(title=f"{title} {start + 1}-{end} of {len(items)} (Page {page + 1}/{total_pages})")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Name", style="bold")
            table.add_column("Count", justify="right")

            for i, (name, count) in enumerate(displayed, start + 1):
                table.add_row(str(i), name, str(count))

            console.print(table)
            nav = "[n]ext | [p]rev | [number] | [text] search"
            if allow_back:
                nav += " | [b]ack"
            console.print(f"[dim]{nav} | [q]uit[/dim]\n")

            choice = Prompt.ask(prompt_text, default="1")
            c = choice.lower().strip()

            if c in ("n", "next"):
                page = min(page + 1, total_pages - 1)
            elif c in ("p", "prev"):
                page = max(page - 1, 0)
            elif c == "q":
                return ("quit", None, page)
            elif c == "b" and allow_back:
                return ("back", None, page)
            elif choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(items):
                    return ("select", items[idx - 1][0], page)
                console.print("[red]Invalid number[/red]")
            else:
                # Search
                matches = self.search_items(choice, items)
                if not matches:
                    console.print(f"[red]No match for '{choice}'[/red]")
                elif len(matches) == 1:
                    return ("select", matches[0][0], page)
                else:
                    console.print(f"\n[bold]Found {len(matches)} matches:[/bold]")
                    for i, (name, count) in enumerate(matches[:10], 1):
                        console.print(f"  {i}. {name} ({count})")
                    sub = Prompt.ask("Select number, or Enter to go back", default="")
                    if sub.isdigit() and 1 <= int(sub) <= min(len(matches), 10):
                        return ("select", matches[int(sub) - 1][0], page)

    def preview_city(self, city: str) -> None:
        """Show preview of selected city."""
        city_businesses = [b for b in self.businesses.values() if b.get("city") == city]
        cat_counts = self.get_category_counts(city)
        top_cats = list(cat_counts.items())[:5]
        samples = random.sample(city_businesses, min(5, len(city_businesses)))

        content = Text()
        content.append(f"Total Restaurants: ", style="bold")
        content.append(f"{len(city_businesses)}\n\n")
        content.append("Top Categories:\n", style="bold")
        for cat, count in top_cats:
            content.append(f"  - {cat}: {count}\n")
        content.append("\nSample Restaurants:\n", style="bold")
        for s in samples:
            content.append(f"  - {s['name']} ({s.get('stars', '?')} stars)\n")

        console.print(Panel(content, title=f"[bold cyan]Preview: {city}[/bold cyan]"))

    def preview_categories(self, categories: List[str], cat_counts: dict) -> None:
        """Show preview of selected categories."""
        filtered = [b for b in self.businesses.values()
                    if b.get("city") == self.city and
                    any(cat in (b.get("categories") or "") for cat in categories)]

        star_dist = Counter(int(b.get("stars", 0)) for b in filtered)
        samples = random.sample(filtered, min(5, len(filtered))) if filtered else []

        content = Text()
        content.append("Selected Categories:\n", style="bold")
        for cat in categories:
            content.append(f"  - {cat} ({cat_counts.get(cat, 0)})\n")
        content.append(f"\nTotal Matching: ", style="bold")
        content.append(f"{len(filtered)}\n\n")
        content.append("Star Distribution:\n", style="bold")
        max_count = max(star_dist.values()) if star_dist else 1
        for star in range(1, 6):
            count = star_dist.get(star, 0)
            bar_len = int((count / max_count) * 15) + 1 if count > 0 else 0
            content.append(f"  {star}★: {'█' * bar_len} ({count})\n")
        if samples:
            content.append("\nSamples:\n", style="bold")
            for s in samples:
                content.append(f"  - {s['name']} ({s.get('stars', '?')}★)\n")

        cats_str = ", ".join(categories[:3])
        if len(categories) > 3:
            cats_str += f" +{len(categories) - 3}"
        console.print(Panel(content, title=f"[bold cyan]{self.city} > {cats_str}[/bold cyan]"))

    def select_city_interactive(self) -> bool:
        """Interactive city selection with preview."""
        all_cities = list(self.get_city_counts().items())

        while True:
            action, selected, _ = self.paginated_select(
                all_cities, "Cities", "Select city", allow_back=False)

            if action == "quit":
                return False
            if action != "select":
                continue

            self.preview_city(selected)
            confirm = Prompt.ask("[C]onfirm / [B]ack", default="c").lower()
            if confirm == "c":
                self.city = selected
                return True

    def parse_category_input(self, input_str: str, available_cats: list) -> List[str]:
        """Parse '1,3,5' or 'Italian, Mexican' into category list."""
        selected = []
        parts = [p.strip() for p in input_str.split(",")]
        for part in parts:
            if not part:
                continue
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(available_cats):
                    selected.append(available_cats[idx][0])
            else:
                for cat, _ in available_cats:
                    if part.lower() in cat.lower():
                        if cat not in selected:
                            selected.append(cat)
                        break
        return selected

    def select_categories_interactive(self) -> Optional[bool]:
        """Interactive category selection. Returns True=confirmed, False=quit, None=back."""
        cat_counts = self.get_category_counts(self.city)
        all_cats = list(cat_counts.items())
        page = 0
        page_size = 20

        while True:
            total_pages = max(1, (len(all_cats) + page_size - 1) // page_size)
            start = page * page_size
            end = min(start + page_size, len(all_cats))
            displayed = all_cats[start:end]

            table = Table(title=f"Categories in {self.city} {start + 1}-{end} of {len(all_cats)} (Page {page + 1}/{total_pages})")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Category", style="bold")
            table.add_column("Count", justify="right")

            for i, (cat, count) in enumerate(displayed, start + 1):
                table.add_row(str(i), cat, str(count))

            console.print(table)
            console.print("[dim][n]ext | [p]rev | [numbers] 1,3,5 | [text] search | [b]ack | [q]uit[/dim]\n")

            choice = Prompt.ask("Select categories", default="1")
            c = choice.lower().strip()

            if c in ("n", "next"):
                page = min(page + 1, total_pages - 1)
                continue
            elif c in ("p", "prev"):
                page = max(page - 1, 0)
                continue
            elif c == "b":
                return None
            elif c == "q":
                return False

            selected_cats = self.parse_category_input(choice, all_cats)
            if not selected_cats:
                console.print("[red]No valid categories selected[/red]")
                continue

            self.preview_categories(selected_cats, cat_counts)

            action = Prompt.ask("[C]onfirm / [B]ack", default="c").lower()
            if action == "c":
                self.categories = selected_cats
                return True

    # ─────────────────────────────────────────────────────────────────────────
    # Scoring and Processing
    # ─────────────────────────────────────────────────────────────────────────

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
            with console.status("[bold green]Generating category keywords..."):
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

        first_5 = reviews[:5]
        remaining = reviews[5:]
        random_5 = random.sample(remaining, min(5, len(remaining))) if remaining else []
        sample_reviews = first_5 + random_5
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

        reason = f"{pct}% - {match_count}/{total_reviews} keyword matches, {stars}*"
        return (biz, pct, reason)

    async def score_businesses(self) -> None:
        """Score businesses by category fit."""
        scored = self.compute_richness_scores()
        console.print(f"\n[bold]Scoring {len(scored)} businesses...[/bold]")

        all_results = []
        above_threshold = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            total_batches = (len(scored) + self.batch_size - 1) // self.batch_size
            task = progress.add_task("Processing batches...", total=total_batches)

            for batch_start in range(0, len(scored), self.batch_size):
                batch = scored[batch_start:batch_start + self.batch_size]
                batch_num = batch_start // self.batch_size + 1
                progress.update(task, description=f"Batch {batch_num}/{total_batches}")

                if self.skip_llm:
                    results = [self.estimate_simple(biz) for biz, _ in batch]
                else:
                    tasks = [self.estimate_category_fit_async(biz) for biz, _ in batch]
                    results = await asyncio.gather(*tasks)

                all_results.extend(results)
                above_threshold = sum(1 for _, pct, _ in all_results if pct >= self.threshold)

                progress.advance(task)

                if above_threshold >= self.target:
                    console.print(f"\n[green]Reached {self.target} above {self.threshold}%. Stopping early.[/green]")
                    break

        all_results.sort(key=lambda x: -x[1])
        self.scored_results = all_results

        console.print(f"[green]Scored {len(all_results)} businesses[/green]")
        console.print(f"[green]Above {self.threshold}%: {above_threshold}[/green]")

    # ─────────────────────────────────────────────────────────────────────────
    # Output
    # ─────────────────────────────────────────────────────────────────────────

    def show_top_results(self, n: int = 20) -> None:
        """Display top results in a table."""
        table = Table(title=f"Top {n} Results")
        table.add_column("#", style="dim")
        table.add_column("Name")
        table.add_column("Score", justify="right")
        table.add_column("Reviews", justify="right")

        for i, (biz, pct, _) in enumerate(self.scored_results[:n], 1):
            reviews = len(self.reviews_by_biz.get(biz["business_id"], []))
            score_style = "green" if pct >= self.threshold else "yellow" if pct >= 50 else "red"
            table.add_row(
                str(i),
                biz.get("name", "")[:40],
                f"[{score_style}]{pct}%[/{score_style}]",
                str(reviews)
            )

        console.print(table)

    def write_output(self) -> None:
        """Write restaurants.jsonl, reviews.jsonl, and meta.json."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        selected = [(biz, pct, reason) for biz, pct, reason in self.scored_results if pct >= self.threshold]
        if len(selected) < self.target:
            selected = self.scored_results[:self.target]

        selected_ids = {biz["business_id"] for biz, _, _ in selected}

        user_ids = set()
        for bid in selected_ids:
            for r in self.reviews_by_biz.get(bid, []):
                user_ids.add(r["user_id"])

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
        console.print(f"[green]Wrote {len(selected)} restaurants to {restaurants_file}[/green]")

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
        console.print(f"[green]Wrote {review_count:,} reviews to {reviews_file}[/green]")

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
        console.print(f"[green]Wrote metadata to {meta_file}[/green]")

    # ─────────────────────────────────────────────────────────────────────────
    # Main Entry
    # ─────────────────────────────────────────────────────────────────────────

    def run_interactive(self) -> bool:
        """Run interactive selection mode. Returns True if successful."""
        console.print(Panel.fit(
            "[bold]Yelp Data Curation[/bold]\n"
            "Select city and categories to curate.",
            border_style="cyan"
        ))

        self.load_business_data()

        # City selection loop
        while True:
            if not self.select_city_interactive():
                return False

            result = self.select_categories_interactive()
            if result is False:
                return False
            elif result is None:
                continue  # Back to city
            else:
                break

        # Get selection name
        default_name = f"{self.city.lower().replace(' ', '_')}_{self.categories[0].lower().replace(' ', '_').replace('&', '')}"
        self.name = Prompt.ask("Selection name", default=default_name)
        self.output_dir = OUTPUT_DIR / self.name

        # Options
        self.skip_llm = Prompt.ask("Use LLM for scoring? [Y/n]", default="y").lower() != "y"
        self.target = int(Prompt.ask("Target restaurants", default="100"))

        return True

    def run(self) -> None:
        """Main entry point."""
        console.print(Panel.fit(
            f"[bold]Curating:[/bold] {self.city} > {', '.join(self.categories)}\n"
            f"[bold]Output:[/bold] {self.output_dir}",
            title="Yelp Data Curation"
        ))

        if not self.businesses:
            self.load_business_data()

        filtered = self.get_filtered_businesses()
        console.print(f"[bold]Found {len(filtered)} matching businesses[/bold]")

        if not filtered:
            console.print("[red]No businesses found. Exiting.[/red]")
            return

        business_ids = {b["business_id"] for b in filtered}
        self.load_reviews(business_ids)

        if not self.skip_llm:
            self.category_keywords = self.generate_category_keywords()
            console.print(f"[dim]Keywords: {', '.join(self.category_keywords[:10])}...[/dim]")
        else:
            self.category_keywords = [cat.lower() for cat in self.categories]

        asyncio.run(self.score_businesses())

        self.show_top_results()
        self.write_output()

        console.print(Panel.fit(
            f"[bold green]Complete![/bold green]\nOutput: {self.output_dir}",
            title="Done"
        ))


def main():
    parser = argparse.ArgumentParser(description="Curate Yelp restaurants")
    parser.add_argument("--name", help="Selection name (e.g., philly_cafes)")
    parser.add_argument("--city", help="City name (e.g., Philadelphia)")
    parser.add_argument("--category", nargs="+", help="Categories")
    parser.add_argument("--target", type=int, default=100, help="Target restaurants")
    parser.add_argument("--threshold", type=int, default=70, help="Min score threshold")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size")
    parser.add_argument("--skip-llm", action="store_true", help="Use heuristic")

    args = parser.parse_args()

    if args.name and args.city and args.category:
        # Non-interactive mode
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
    else:
        # Interactive mode
        curator = Curator(
            target=args.target,
            threshold=args.threshold,
            batch_size=args.batch_size,
            skip_llm=args.skip_llm
        )
        if curator.run_interactive():
            curator.run()


if __name__ == "__main__":
    main()
