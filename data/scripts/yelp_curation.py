#!/usr/bin/env python3
"""Human-in-the-Loop Yelp data curation tool for benchmark dataset creation."""

import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path for utils import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from utils.llm import call_llm

# File paths
RAW_DIR = Path(__file__).parent.parent / "raw"
BUSINESS_FILE = RAW_DIR / "yelp_academic_dataset_business.json"
REVIEW_FILE = RAW_DIR / "yelp_academic_dataset_review.json"
OUTPUT_FILE = Path(__file__).parent.parent / "yelp_selections.jsonl"


class YelpCurator:
    """Human-in-the-loop curation tool for Yelp data."""

    def __init__(self):
        self.console = Console()
        self.businesses: Dict[str, dict] = {}
        self.reviews_by_biz: Dict[str, List[dict]] = defaultdict(list)
        self.selected_city: Optional[str] = None
        self.selected_categories: List[str] = []  # Multi-category support
        self.selections: List[dict] = []

    def load_business_data(self) -> None:
        """Load all restaurant businesses from Yelp data."""
        if not BUSINESS_FILE.exists():
            self.console.print(f"[red]Error: Business file not found: {BUSINESS_FILE}[/red]")
            sys.exit(1)

        with self.console.status("[bold green]Loading business data..."):
            with open(BUSINESS_FILE) as f:
                for line in f:
                    biz = json.loads(line)
                    cats = biz.get("categories", "") or ""
                    if "Restaurant" in cats:
                        self.businesses[biz["business_id"]] = biz

        self.console.print(f"[green]Loaded {len(self.businesses)} restaurants[/green]")

    def load_reviews_for_businesses(self, business_ids: set) -> None:
        """Load reviews only for specified businesses (memory optimization)."""
        if not REVIEW_FILE.exists():
            self.console.print(f"[red]Error: Review file not found: {REVIEW_FILE}[/red]")
            sys.exit(1)

        self.reviews_by_biz.clear()
        with self.console.status("[bold green]Loading reviews for selected businesses..."):
            with open(REVIEW_FILE) as f:
                for i, line in enumerate(f):
                    if i % 500000 == 0 and i > 0:
                        self.console.print(f"  [dim]Processed {i:,} reviews...[/dim]")
                    review = json.loads(line)
                    bid = review["business_id"]
                    if bid in business_ids:
                        self.reviews_by_biz[bid].append(review)

        total_reviews = sum(len(r) for r in self.reviews_by_biz.values())
        self.console.print(f"[green]Loaded {total_reviews:,} reviews for {len(self.reviews_by_biz)} restaurants[/green]")

    def get_city_counts(self) -> Dict[str, int]:
        """Count restaurants per city."""
        counts = defaultdict(int)
        for biz in self.businesses.values():
            city = biz.get("city", "Unknown")
            counts[city] += 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))

    def get_category_counts(self, city: str) -> Dict[str, int]:
        """Count categories within a city."""
        counts = defaultdict(int)
        for biz in self.businesses.values():
            if biz.get("city") != city:
                continue
            cats = biz.get("categories", "") or ""
            for cat in cats.split(", "):
                cat = cat.strip()
                if cat and cat != "Restaurants":
                    counts[cat] += 1
        return dict(sorted(counts.items(), key=lambda x: -x[1]))

    def get_filtered_businesses(self) -> List[dict]:
        """Get businesses matching selected city and ANY of the selected categories."""
        results = []
        for biz in self.businesses.values():
            if biz.get("city") != self.selected_city:
                continue
            cats = biz.get("categories", "") or ""
            # Match ANY of selected categories
            if any(cat in cats for cat in self.selected_categories):
                results.append(biz)
        return results

    def preview_city(self, city: str) -> None:
        """Show preview of selected city."""
        city_businesses = [b for b in self.businesses.values() if b.get("city") == city]
        cat_counts = self.get_category_counts(city)
        top_cats = list(cat_counts.items())[:5]
        samples = random.sample(city_businesses, min(5, len(city_businesses)))

        panel_content = Text()
        panel_content.append(f"Total Restaurants: ", style="bold")
        panel_content.append(f"{len(city_businesses)}\n\n")
        panel_content.append("Top Categories:\n", style="bold")
        for cat, count in top_cats:
            panel_content.append(f"  - {cat}: {count}\n")
        panel_content.append("\nSample Restaurants:\n", style="bold")
        for s in samples:
            panel_content.append(f"  - {s['name']} ({s.get('stars', '?')} stars)\n")

        self.console.print(Panel(panel_content, title=f"[bold cyan]Preview: {city}[/bold cyan]"))

    def preview_category(self, category: str) -> None:
        """Show preview of selected category within city."""
        filtered = [b for b in self.businesses.values()
                    if b.get("city") == self.selected_city and category in (b.get("categories") or "")]

        # Star distribution
        star_dist = defaultdict(int)
        for b in filtered:
            stars = b.get("stars", 0)
            star_dist[int(stars)] += 1

        samples = random.sample(filtered, min(5, len(filtered)))

        panel_content = Text()
        panel_content.append(f"Matching Restaurants: ", style="bold")
        panel_content.append(f"{len(filtered)}\n\n")
        panel_content.append("Star Distribution:\n", style="bold")
        for star in range(1, 6):
            count = star_dist.get(star, 0)
            bar = "█" * min(count, 20)
            panel_content.append(f"  {star}★: {bar} ({count})\n")
        panel_content.append("\nSample Restaurants:\n", style="bold")
        for s in samples:
            panel_content.append(f"  - {s['name']} ({s.get('stars', '?')}★, {s.get('review_count', 0)} reviews)\n")

        self.console.print(Panel(panel_content, title=f"[bold cyan]Preview: {self.selected_city} > {category}[/bold cyan]"))

    def preview_categories(self, categories: List[str], cat_counts: dict) -> None:
        """Show preview of multiple selected categories within city."""
        # Get all matching businesses
        filtered = [b for b in self.businesses.values()
                    if b.get("city") == self.selected_city and
                    any(cat in (b.get("categories") or "") for cat in categories)]

        # Star distribution
        star_dist = defaultdict(int)
        for b in filtered:
            stars = b.get("stars", 0)
            star_dist[int(stars)] += 1

        samples = random.sample(filtered, min(5, len(filtered))) if filtered else []

        panel_content = Text()
        panel_content.append("Selected Categories:\n", style="bold")
        for cat in categories:
            count = cat_counts.get(cat, 0)
            panel_content.append(f"  - {cat} ({count})\n")
        panel_content.append(f"\nTotal Matching Restaurants: ", style="bold")
        panel_content.append(f"{len(filtered)}\n\n")
        panel_content.append("Star Distribution:\n", style="bold")
        for star in range(1, 6):
            count = star_dist.get(star, 0)
            bar = "█" * min(count, 20)
            panel_content.append(f"  {star}★: {bar} ({count})\n")
        if samples:
            panel_content.append("\nSample Restaurants:\n", style="bold")
            for s in samples:
                panel_content.append(f"  - {s['name']} ({s.get('stars', '?')}★, {s.get('review_count', 0)} reviews)\n")

        cats_str = ", ".join(categories[:3])
        if len(categories) > 3:
            cats_str += f" +{len(categories) - 3} more"
        self.console.print(Panel(panel_content, title=f"[bold cyan]Preview: {self.selected_city} > {cats_str}[/bold cyan]"))

    def search_items(self, query: str, items: list) -> list:
        """Search items by name (case-insensitive partial match)."""
        query_lower = query.lower()
        return [(name, count) for name, count in items if query_lower in name.lower()]

    def paginated_select(self, items: list, title: str, prompt_text: str,
                         page_size: int = 20, allow_back: bool = False) -> tuple:
        """Reusable paginated selection. Returns (action, selection, page).

        Actions: 'select' (with selection), 'back', 'quit', or None (continue loop).
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

            self.console.print(table)
            nav = "[n]ext | [p]rev | [number] | [text] search"
            if allow_back:
                nav += " | [b]ack"
            self.console.print(f"[dim]{nav} | [q]uit[/dim]\n")

            choice = Prompt.ask(prompt_text, default="1")
            c = choice.lower()

            # Navigation
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
                self.console.print("[red]Invalid number[/red]")
            else:
                # Search
                matches = self.search_items(choice, items)
                if not matches:
                    self.console.print(f"[red]No match for '{choice}'[/red]")
                elif len(matches) == 1:
                    return ("select", matches[0][0], page)
                else:
                    self.console.print(f"\n[bold]Found {len(matches)} matches:[/bold]")
                    for i, (name, count) in enumerate(matches[:10], 1):
                        self.console.print(f"  {i}. {name} ({count})")
                    sub = Prompt.ask("Select number, or Enter to go back", default="")
                    if sub.isdigit() and 1 <= int(sub) <= min(len(matches), 10):
                        return ("select", matches[int(sub) - 1][0], page)
                    self.console.print("[yellow]Returning to list...[/yellow]")

    def select_city_loop(self) -> bool:
        """Iterative city selection with preview and confirm."""
        all_cities = list(self.get_city_counts().items())

        while True:
            action, selected, _ = self.paginated_select(
                all_cities, "Cities", "Select city", allow_back=False)

            if action == "quit":
                return False
            if action != "select":
                continue

            self.preview_city(selected)
            confirm = Prompt.ask("[C]onfirm / [A]djust / [Q]uit",
                                 choices=["c", "a", "q", "C", "A", "Q"], default="c").lower()
            if confirm == "q":
                return False
            if confirm == "c":
                self.selected_city = selected
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
                # Match by name (partial, case-insensitive)
                for cat, _ in available_cats:
                    if part.lower() in cat.lower():
                        if cat not in selected:
                            selected.append(cat)
                        break
        return selected

    def select_category_loop(self) -> bool:
        """Iterative category selection with pagination. Supports multi-select."""
        cat_counts = self.get_category_counts(self.selected_city)
        all_cats = list(cat_counts.items())
        page = 0
        page_size = 20

        while True:
            total_pages = max(1, (len(all_cats) + page_size - 1) // page_size)
            start = page * page_size
            end = min(start + page_size, len(all_cats))
            displayed = all_cats[start:end]

            table = Table(title=f"Categories in {self.selected_city} {start + 1}-{end} of {len(all_cats)} (Page {page + 1}/{total_pages})")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Category", style="bold")
            table.add_column("Count", justify="right")

            for i, (cat, count) in enumerate(displayed, start + 1):
                table.add_row(str(i), cat, str(count))

            self.console.print(table)
            self.console.print('[dim][n]ext | [p]rev | "1,3,5" or "Italian, Mexican" | [b]ack | [q]uit[/dim]\n')

            choice = Prompt.ask("Select categories", default="1")
            c = choice.lower()

            # Navigation
            if c in ("n", "next"):
                page = min(page + 1, total_pages - 1)
                continue
            elif c in ("p", "prev"):
                page = max(page - 1, 0)
                continue
            elif c == "b":
                self.selected_city = None
                return None
            elif c == "q":
                return False

            # Parse multi-selection (works across all pages)
            selected_cats = self.parse_category_input(choice, all_cats)
            if not selected_cats:
                self.console.print("[red]No valid categories selected[/red]")
                continue

            self.console.print(f"\n[green]Selected {len(selected_cats)} categories:[/green]")
            for cat in selected_cats:
                self.console.print(f"  - {cat} ({cat_counts.get(cat, 0)})")

            self.preview_categories(selected_cats, cat_counts)

            action = Prompt.ask("[C]onfirm / [A]djust / [B]ack / [Q]uit",
                                choices=["c", "a", "b", "q", "C", "A", "B", "Q"], default="c").lower()
            if action == "q":
                return False
            elif action == "b":
                self.selected_city = None
                return None
            elif action == "c":
                self.selected_categories = selected_cats
                return True

    def display_restaurant(self, biz: dict) -> None:
        """Display restaurant info in a panel."""
        attrs = biz.get("attributes") or {}

        content = Text()
        content.append(f"City: {biz.get('city', 'N/A')}    ", style="dim")
        cats_str = ", ".join(self.selected_categories[:3])
        if len(self.selected_categories) > 3:
            cats_str += f" +{len(self.selected_categories) - 3}"
        content.append(f"Categories: {cats_str}\n\n", style="dim")

        content.append("Attributes:\n", style="bold")
        for key, val in list(attrs.items())[:10]:
            content.append(f"  - {key}: {val}\n")
        if len(attrs) > 10:
            content.append(f"  ... and {len(attrs) - 10} more\n", style="dim")

        title = f"[bold]{biz['name']}[/bold] ({biz.get('stars', '?')}★, {biz.get('review_count', 0)} reviews)"
        self.console.print(Panel(content, title=title))

    def llm_check_restaurant(self, biz: dict) -> str:
        """Ask LLM to evaluate restaurant data richness."""
        attrs = biz.get("attributes") or {}
        system = "You are a data quality evaluator for ML datasets."
        prompt = f"""Evaluate if this restaurant has "rich" data for a benchmark:

Name: {biz['name']}
Stars: {biz.get('stars', 'N/A')}
Review Count: {biz.get('review_count', 0)}
Categories: {biz.get('categories', 'N/A')}
Attributes: {json.dumps(attrs, indent=2)}

Rich data means: multiple interesting attributes, potential for ambiguity,
varied review sentiments likely. Answer YES/NO and explain briefly (2-3 sentences)."""

        with self.console.status("[bold blue]Asking LLM..."):
            response = call_llm(prompt, system=system)
        return response

    def display_review(self, review: dict, idx: int) -> None:
        """Display a single review."""
        text = review.get("text", "")
        if len(text) > 500:
            text = text[:500] + "..."

        table = Table(show_header=False, box=None)
        table.add_column("Label", style="bold cyan", width=12)
        table.add_column("Value")

        table.add_row("Review #", str(idx + 1))
        table.add_row("User ID", review.get("user_id", "N/A")[:16] + "...")
        table.add_row("Stars", f"{review.get('stars', '?')}★")
        table.add_row("Date", review.get("date", "N/A")[:10])
        table.add_row("Useful", str(review.get("useful", 0)))

        self.console.print(table)
        self.console.print(Panel(text, title="Review Text"))

    def llm_check_review(self, review: dict) -> str:
        """Ask LLM to evaluate review quality."""
        system = "You are a data quality evaluator for ML datasets."
        prompt = f"""Is this review detailed and specific enough for ML evaluation?

Review ({review.get('stars', '?')} stars):
"{review.get('text', '')[:1000]}"

Good reviews have: specific details, clear opinions on food/service/ambiance,
useful for sentiment analysis. Answer YES/NO with brief reasoning (2-3 sentences)."""

        with self.console.status("[bold blue]Asking LLM..."):
            response = call_llm(prompt, system=system)
        return response

    def run_review_loop(self, biz: dict) -> List[dict]:
        """Inner loop for selecting reviews from a restaurant."""
        bid = biz["business_id"]
        reviews = self.reviews_by_biz.get(bid, [])

        if not reviews:
            self.console.print("[yellow]No reviews found for this restaurant[/yellow]")
            return []

        selected_reviews = []
        random.shuffle(reviews)

        for idx, review in enumerate(reviews):
            self.console.print(f"\n[bold]--- Review {idx + 1} of {len(reviews)} ---[/bold]")
            self.display_review(review, idx)

            action = Prompt.ask(
                "[K]eep / [S]kip / [L]LM Check / [D]one",
                choices=["k", "s", "l", "d", "K", "S", "L", "D"],
                default="s"
            ).lower()

            if action == "d":
                break
            elif action == "s":
                continue
            elif action == "l":
                rationale = self.llm_check_review(review)
                self.console.print(f"\n[bold blue]LLM says:[/bold blue] {rationale}\n")

                user_notes = Prompt.ask("Add your notes (or press Enter to skip)", default="")

                keep = Confirm.ask("Keep this review?", default=True)
                if keep:
                    selected_reviews.append({
                        "review_id": review.get("review_id"),
                        "user_id": review.get("user_id"),
                        "text": review.get("text"),
                        "stars": review.get("stars"),
                        "date": review.get("date"),
                        "useful": review.get("useful", 0),
                        "user_notes": user_notes if user_notes else None,
                        "llm_rationale": rationale
                    })
                    self.console.print("[green]Review kept[/green]")
            elif action == "k":
                selected_reviews.append({
                    "review_id": review.get("review_id"),
                    "user_id": review.get("user_id"),
                    "text": review.get("text"),
                    "stars": review.get("stars"),
                    "date": review.get("date"),
                    "useful": review.get("useful", 0),
                    "user_notes": None,
                    "llm_rationale": None
                })
                self.console.print("[green]Review kept[/green]")

        self.console.print(f"\n[bold]Selected {len(selected_reviews)} reviews for this restaurant[/bold]")
        return selected_reviews

    def run_restaurant_loop(self) -> None:
        """Main loop for selecting restaurants."""
        filtered = self.get_filtered_businesses()
        random.shuffle(filtered)

        self.console.print(f"\n[bold]Starting restaurant selection ({len(filtered)} candidates)[/bold]\n")

        for idx, biz in enumerate(filtered):
            self.console.print(f"\n[bold cyan]═══ Restaurant {idx + 1} of {len(filtered)} ═══[/bold cyan]")
            self.display_restaurant(biz)

            action = Prompt.ask(
                "[S]kip / [L]LM Check / [K]eep / [Q]uit",
                choices=["s", "l", "k", "q", "S", "L", "K", "Q"],
                default="s"
            ).lower()

            if action == "q":
                break
            elif action == "s":
                continue
            elif action == "l":
                rationale = self.llm_check_restaurant(biz)
                self.console.print(f"\n[bold blue]LLM says:[/bold blue] {rationale}\n")

                user_notes = Prompt.ask("Add your notes (or press Enter to skip)", default="")

                keep = Confirm.ask("Keep this restaurant?", default=True)
                if keep:
                    reviews = self.run_review_loop(biz)
                    if reviews:
                        self.save_selection(biz, reviews, user_notes, rationale)
            elif action == "k":
                reviews = self.run_review_loop(biz)
                if reviews:
                    self.save_selection(biz, reviews, None, None)

    def save_selection(self, biz: dict, reviews: List[dict],
                       user_notes: Optional[str] = None,
                       llm_rationale: Optional[str] = None) -> None:
        """Save a curated selection to the output file."""
        cats = (biz.get("categories") or "").split(", ")
        cats = [c.strip() for c in cats if c.strip()]

        selection = {
            "item_id": biz["business_id"],
            "item_name": biz["name"],
            "city": biz.get("city"),
            "categories": cats,
            "stars": biz.get("stars"),
            "review_count": biz.get("review_count"),
            "attributes": biz.get("attributes"),
            "user_notes": user_notes,
            "llm_rationale": llm_rationale,
            "selected_reviews": reviews
        }

        # Ensure output directory exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Append to file
        with open(OUTPUT_FILE, "a") as f:
            f.write(json.dumps(selection) + "\n")

        self.selections.append(selection)
        self.console.print(f"[green]Saved selection to {OUTPUT_FILE}[/green]")
        self.console.print(f"[dim]Total selections this session: {len(self.selections)}[/dim]")

    def run(self) -> None:
        """Main entry point for the curation tool."""
        self.console.print(Panel.fit(
            "[bold]Yelp Data Curation Tool[/bold]\n"
            "Human-in-the-loop selection for benchmark datasets",
            border_style="cyan"
        ))

        # Load business data
        self.load_business_data()

        # City selection loop (with back navigation)
        while True:
            if not self.select_city_loop():
                self.console.print("[yellow]Exiting...[/yellow]")
                return

            # Category selection loop
            result = self.select_category_loop()
            if result is False:  # Quit
                self.console.print("[yellow]Exiting...[/yellow]")
                return
            elif result is None:  # Back to city
                continue
            else:  # Confirmed
                break

        # Load reviews for filtered businesses
        filtered = self.get_filtered_businesses()
        business_ids = {b["business_id"] for b in filtered}
        self.load_reviews_for_businesses(business_ids)

        # Run main restaurant selection loop
        self.run_restaurant_loop()

        # Summary
        self.console.print("\n" + "═" * 50)
        self.console.print(f"[bold green]Session complete![/bold green]")
        self.console.print(f"Total selections: {len(self.selections)}")
        self.console.print(f"Output file: {OUTPUT_FILE}")


def main():
    curator = YelpCurator()
    curator.run()


if __name__ == "__main__":
    main()
