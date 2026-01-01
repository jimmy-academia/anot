"""
Aggregation utilities for benchmark runs.
Computes mean/std across multiple runs.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, Any, List

from rich.console import Console
from rich.table import Table

# Base results directory
BENCHMARK_DIR = Path("results") / "benchmarks"


def aggregate_benchmark_runs(method: str, data: str, selection_name: str) -> Dict[str, Any]:
    """
    Aggregate stats across all runs for a benchmark config.

    Args:
        method: Method name (e.g., 'cot')
        data: Data name (e.g., 'yelp')
        selection_name: Selection name (e.g., 'selection_1')

    Returns:
        Summary dict with mean/std and per-run stats
    """
    parent = BENCHMARK_DIR / f"{method}_{data}"
    if not parent.exists():
        return {"runs": 0, "error": "No benchmark directory found"}

    run_dirs = sorted(parent.glob(f"{selection_name}_run_*/"))
    if not run_dirs:
        return {"runs": 0, "error": "No runs found"}

    # Load stats from each run's config.json
    all_stats = []
    for d in run_dirs:
        config_path = d / "config.json"
        if not config_path.exists():
            continue
        with open(config_path) as f:
            config = json.load(f)
        if "stats" in config:
            all_stats.append(config["stats"])

    if not all_stats:
        return {"runs": 0, "error": "No stats found in runs"}

    # Determine stats type and compute aggregates
    summary = _aggregate_stats(all_stats)
    summary["runs"] = len(all_stats)
    summary["method"] = method
    summary["data"] = data
    summary["selection"] = selection_name

    # Save summary.json in parent dir
    summary_path = parent / f"{selection_name}_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    return summary


def _aggregate_stats(all_stats: List[Dict]) -> Dict[str, Any]:
    """
    Aggregate stats list, handling both ranking and per-item modes.
    """
    # Check if ranking mode (has hits_at)
    if "hits_at" in all_stats[0]:
        return _aggregate_ranking_stats(all_stats)
    else:
        return _aggregate_accuracy_stats(all_stats)


def _aggregate_ranking_stats(all_stats: List[Dict]) -> Dict[str, Any]:
    """Aggregate ranking mode stats (Hits@K)."""
    k = all_stats[0].get("k", 5)

    # Collect accuracies for each K
    hits_at_summary = {}
    for j in range(1, k + 1):
        accuracies = [s["hits_at"][str(j)]["accuracy"] for s in all_stats if str(j) in s.get("hits_at", {})]
        if accuracies:
            hits_at_summary[j] = {
                "mean": statistics.mean(accuracies),
                "std": statistics.stdev(accuracies) if len(accuracies) > 1 else 0.0,
                "values": accuracies,
            }

    return {
        "type": "ranking",
        "k": k,
        "hits_at": hits_at_summary,
        "per_run": all_stats,
    }


def _aggregate_accuracy_stats(all_stats: List[Dict]) -> Dict[str, Any]:
    """Aggregate per-item accuracy stats."""
    accuracies = []
    for s in all_stats:
        total = s.get("total", 0)
        correct = s.get("correct", 0)
        if total > 0:
            accuracies.append(correct / total)

    return {
        "type": "accuracy",
        "mean": statistics.mean(accuracies) if accuracies else 0.0,
        "std": statistics.stdev(accuracies) if len(accuracies) > 1 else 0.0,
        "values": accuracies,
        "per_run": all_stats,
    }


def print_summary(summary: Dict[str, Any]):
    """Print aggregated summary using rich tables."""
    console = Console()

    if summary.get("error"):
        console.print(f"[red]{summary['error']}[/red]")
        return

    runs = summary.get("runs", 0)
    console.print(f"\n[bold]Benchmark Summary[/bold] ({runs} run{'s' if runs != 1 else ''})")
    console.print(f"  Method: {summary.get('method', 'N/A')}")
    console.print(f"  Data: {summary.get('data', 'N/A')}")
    console.print(f"  Selection: {summary.get('selection', 'N/A')}")

    if summary.get("type") == "ranking":
        table = Table(title="Hits@K Aggregated Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Mean", style="green")
        table.add_column("Std", style="yellow")
        table.add_column("Values", style="dim")

        for k, stats in summary.get("hits_at", {}).items():
            values_str = ", ".join(f"{v:.4f}" for v in stats["values"])
            table.add_row(
                f"Hits@{k}",
                f"{stats['mean']:.4f}",
                f"{stats['std']:.4f}",
                values_str
            )
        console.print(table)

    elif summary.get("type") == "accuracy":
        values_str = ", ".join(f"{v:.4f}" for v in summary.get("values", []))
        console.print(f"\n[bold]Overall Accuracy[/bold]")
        console.print(f"  Mean: {summary.get('mean', 0):.4f}")
        console.print(f"  Std:  {summary.get('std', 0):.4f}")
        console.print(f"  Values: [{values_str}]")
