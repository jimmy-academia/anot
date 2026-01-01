#!/usr/bin/env python3
"""
Auto-commit monitor - checks for changes at intervals
and commits when significant changes are detected.

Usage:
    python scripts/auto_commit.py [--interval 600] [--rounds 6] [--threshold 10]
"""

import argparse
import subprocess
import time
import re
from datetime import datetime

def get_diff_stats(repo_path="."):
    """Get lines added/removed from git diff."""
    result = subprocess.run(
        ["git", "diff", "--stat"],
        capture_output=True, text=True, cwd=repo_path
    )
    match = re.search(r'(\d+) insertion.*?(\d+) deletion', result.stdout)
    if match:
        return int(match.group(1)), int(match.group(2))
    ins = re.search(r'(\d+) insertion', result.stdout)
    dels = re.search(r'(\d+) deletion', result.stdout)
    return (int(ins.group(1)) if ins else 0, int(dels.group(1)) if dels else 0)

def get_changed_files(repo_path="."):
    """Get list of modified files."""
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True, text=True, cwd=repo_path
    )
    return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]

def get_untracked_files(repo_path="."):
    """Get list of untracked files."""
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, cwd=repo_path
    )
    return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]

def generate_commit_message(changed_files, insertions, deletions):
    """Generate descriptive commit message from diff."""
    categories = {}
    for f in changed_files:
        cat = f.split('/')[0] if '/' in f else 'root'
        categories.setdefault(cat, []).append(f)

    if len(changed_files) == 1:
        msg = f"Update {changed_files[0]}"
    elif len(categories) == 1:
        cat = list(categories.keys())[0]
        msg = f"Update {cat}/ ({len(changed_files)} files)"
    else:
        msg = f"Update {', '.join(categories.keys())}"

    msg += f"\n\n+{insertions}/-{deletions} lines"
    msg += f"\n\n🤖 Auto-commit at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    return msg

def commit_changes(threshold=10, repo_path="."):
    """Stage and commit all changes if above threshold."""
    changed = get_changed_files(repo_path)
    untracked = get_untracked_files(repo_path)
    insertions, deletions = get_diff_stats(repo_path)

    total_lines = insertions + deletions
    all_files = changed + untracked

    if not all_files:
        return False, "No changes"

    if total_lines < threshold and not untracked:
        return False, f"Below threshold ({total_lines} < {threshold} lines)"

    subprocess.run(["git", "add", "-A"], cwd=repo_path)
    msg = generate_commit_message(all_files, insertions, deletions)
    result = subprocess.run(
        ["git", "commit", "-m", msg],
        capture_output=True, text=True, cwd=repo_path
    )

    if result.returncode == 0:
        return True, f"Committed: {len(all_files)} files, +{insertions}/-{deletions}"
    return False, result.stderr.strip()

def monitor(interval=600, rounds=6, threshold=10):
    """Main monitoring loop."""
    print(f"Auto-commit monitor started")
    print(f"  Interval: {interval}s ({interval//60} min)")
    print(f"  Rounds: {rounds}")
    print(f"  Threshold: {threshold} lines")
    print(f"  Total time: ~{interval * rounds // 60} min")
    print()

    for i in range(rounds):
        try:
            success, msg = commit_changes(threshold)
            timestamp = datetime.now().strftime('%H:%M:%S')
            status = "✓" if success else "-"
            print(f"[{timestamp}] Round {i+1}/{rounds}: {status} {msg}")
        except Exception as e:
            print(f"[ERROR] Round {i+1}: {e}")

        if i < rounds - 1:
            time.sleep(interval)

    print(f"\nMonitor complete ({rounds} rounds)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-commit monitor")
    parser.add_argument("--interval", type=int, default=600, help="Seconds between checks")
    parser.add_argument("--rounds", type=int, default=6, help="Number of check rounds")
    parser.add_argument("--threshold", type=int, default=10, help="Min lines to trigger commit")
    args = parser.parse_args()

    monitor(args.interval, args.rounds, args.threshold)
