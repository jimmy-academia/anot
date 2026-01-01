# Auto-Commit Monitor

Monitors codebase and auto-commits when significant changes detected.

## Quick Start

```bash
# Run for 1 hour (6 rounds, 10 min each)
python scripts/auto_commit.py

# Or with custom settings
python scripts/auto_commit.py --interval 600 --rounds 6 --threshold 10
```

## Configuration

| Param | Default | Description |
|-------|---------|-------------|
| `--interval` | 600 | Seconds between checks (10 min) |
| `--rounds` | 6 | Number of check rounds |
| `--threshold` | 10 | Min lines changed to trigger commit |

## Commit Message Format

```
Update utils/ (3 files)

+45/-12 lines

🤖 Auto-commit at 2025-01-01 12:30
```
