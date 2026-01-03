# ANoT Architecture

ANoT (Adaptive Network of Thought) is a three-phase evaluation method for ranking tasks over structured multi-source data.

**Performance:** 70% Hits@1 vs CoT's 44.74% on philly_cafes (10 candidates)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User Request                          │
│     "I need a cafe with a drive-thru option"            │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Phase 1: ReAct Exploration                 │
│  • Discover data structure via tools (count, keys, etc) │
│  • Find relevant attributes (e.g., DriveThru)           │
│  • Generate global plan with N branches                 │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Phase 2: LWT Expansion (Parallel)          │
│  • For each item, LLM generates evaluation step         │
│  • Semantic scoring prompts with actual attribute values│
│  • Output: (idx)=LLM("prompt. Output: <score>")         │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Phase 3: Parallel Execution                │
│  • Execute all LWT steps in parallel                    │
│  • Parse scores (0-10 scale)                            │
│  • Rank items by score, return top-k                    │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Final Ranking                          │
│            [6, 2, 9, 1, 4] (top-5 indices)              │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: ReAct Exploration

**Goal:** Discover data structure and generate a global plan.

The LLM explores the data using lightweight tools (executed in Python, not by LLM):

| Tool | Description | Example |
|------|-------------|---------|
| `count(path)` | Length of array/dict | `count("items")` → `10` |
| `keys(path)` | List of keys at path | `keys("items[0]")` → `["item_id", "attributes", ...]` |
| `union_keys(path)` | Union of keys across items | `union_keys("items[*].attributes")` → `["DriveThru", "WiFi", ...]` |
| `sample(path)` | Sample value (truncated) | `sample("items[0].item_name")` → `"Cafe Roma"` |

**ReAct Loop:**
```
THOUGHT: I need to find items with drive-thru...
ACTION: union_keys("items[*].attributes")
RESULT: ["DriveThru", "WiFi", "NoiseLevel", ...]
THOUGHT: Found DriveThru attribute!
PLAN:
N = 10
RELEVANT_ATTR = DriveThru
(0) = evaluate item 0: check [attributes][DriveThru]
...
(10) = aggregate scores, return top-5
```

**Output:** Structured plan with:
- `n_items`: Number of items
- `relevant_attr`: Key attribute to check
- `branches`: List of (idx, instruction) tuples

---

## Phase 2: LWT Expansion (Parallel)

**Goal:** Generate intelligent, semantic evaluation prompts for each item using LLM.

For each item, the LLM generates an LWT step that:
1. Understands the user's request context
2. Evaluates actual attribute values semantically
3. Produces a 0-10 score based on match quality

**Example Expansion:**

For user request "I need a cafe with a drive-thru option":

```
(0)=LLM("Evaluate Tria Cafe. DriveThru: not present. No drive-thru means poor fit. Score 0-10. Output: <score>")
(1)=LLM("Evaluate Front Street Cafe. DriveThru: not present. TakeOut: True. Partial fit. Score 0-10. Output: <score>")
...
(5)=LLM("Evaluate Milkcrate Cafe. DriveThru: True. GoodForKids: True. Perfect match! Score 0-10. Output: <score>")
```

**Prompt Template:** `EXPAND_BRANCH_PROMPT` includes:
- User request context
- Item name and index
- Actual attribute values (JSON)
- Sample reviews
- LWT syntax instructions

**Parallelization:** All items expand concurrently via `asyncio.gather()`.

---

## Phase 3: Parallel Execution

**Goal:** Execute all LWT steps and aggregate results.

**Execution Model:**
- Uses `asyncio` for parallel LLM calls
- DAG-based layer execution (independent steps run concurrently)
- Results cached by step index
- Per-step token usage captured after parallel execution

**Scoring Scale:**

| Score | Meaning |
|-------|---------|
| 0-2   | Poor match |
| 3-4   | Weak match |
| 5-6   | Moderate match |
| 7-8   | Good match |
| 9-10  | Excellent match |

**Score Parsing:** `parse_score()` handles varied LLM output formats:
- Direct number: `5`
- XML tags: `<5>` or `<score>5</score>`
- Fraction: `4/10`
- Score prefix: `Score: 5` or `Output: 5`
- With explanation: `5 — explanation here`

**Output:** Top-K indices ranked by score (descending), then by index (ascending for ties).

---

## Debug Mode

Control debug output via `ANOT_DEBUG` environment variable:

| Level | Name | Output |
|-------|------|--------|
| 0 | OFF | Rich table display only |
| 1 | SUMMARY | Phase transitions, final scores |
| 2 | VERBOSE | Per-item progress, LWT steps |
| 3 | FULL | Complete LLM prompts and responses |

**Usage:**
```bash
# Run with verbose debug
ANOT_DEBUG=2 python main.py --method anot --data philly_cafes --candidates 10 --limit 10

# Monitor in another terminal
tail -f results/benchmarks/anot_philly_cafes/clean/run_1/anot_debug.log
```

**Debug Output Format:**
```
[HH:MM:SS.mmm] [P1:R00] Starting exploration: I need a cafe...
[HH:MM:SS.mmm] [P1:R00] Plan: attr=DriveThru, branches=11
[HH:MM:SS.mmm] [P2:R00] Expanding 10 items (parallel)...
[HH:MM:SS.mmm] [P2:R00] Item 5 (Milkcrate Cafe): (5)=LLM("Evaluate...")
[HH:MM:SS.mmm] [P3:R00] Executing 11 steps in 2 layers...
[HH:MM:SS.mmm] [P3:R00] Final scores: [('Milkcrate Cafe', 9), ...]
[HH:MM:SS.mmm] [P3:R00] Final ranking: 6,2,9,1,3
```

---

## Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `phase1_explore()` | `methods/anot.py:686` | ReAct-style data exploration |
| `phase2_expand()` | `methods/anot.py:946` | Parallel LWT generation |
| `phase3_execute()` | `methods/anot.py:1089` | Parallel LWT execution |
| `parse_score()` | `methods/anot.py:124` | Robust 0-10 score extraction |
| `execute_tool()` | `methods/anot.py:196` | Data exploration tools |
| `_expand_branch_async()` | `methods/anot.py:884` | Async item expansion |

---

## LWT Syntax

LWT (Lightweight Template) is the execution script format:

```
(0)=LLM("Evaluate Milkcrate Cafe for drive-thru. DriveThru=True. Score 0-10.")
(1)=LLM("Evaluate Tria Cafe for drive-thru. DriveThru=False. Score 0-10.")
...
(9)=LLM("Evaluate Chapterhouse for drive-thru. DriveThru=False. Score 0-10.")
(10)=LLM("Scores: {0}, {1}, {2}, ..., {9}. Return top-5 indices sorted by score.")
```

**Variable Substitution:** `{idx}` is replaced with cached result from step `idx`.

---

## Example Trace

For request "I need a cafe with a drive-thru option":

```
Phase 1 (32s):
  → count("items") = 10
  → keys("items[0]") = ["item_id", "attributes", ...]
  → union_keys("items[*].attributes") = ["DriveThru", "WiFi", ...]
  → Plan: N=10, RELEVANT_ATTR=DriveThru, branches=11

Phase 2 (45s):
  → 10 async LLM calls for item expansion
  → Generated semantic prompts with actual attribute values
  → Example: (5)=LLM("Milkcrate Cafe. DriveThru=True, GoodForKids=True. Score: 9")

Phase 3 (15s):
  → 11 steps executed in 2 layers (parallel)
  → Scores: [2, 1, 1, 2, 1, 9, 1, 2, 1, 2]
  → Top-5: [6, 1, 4, 8, 10] (item 6 = Milkcrate Cafe with DriveThru=True)
```

---

## Key Files

| File | Purpose |
|------|---------|
| `methods/anot.py` | Main ANoT implementation (~1300 lines) |
| `methods/shared.py` | Shared utilities (parse_script, build_execution_layers) |
| `prompts/task_descriptions.py` | Standard task descriptions |
| `utils/llm.py` | LLM call wrappers (sync and async) |

---

## Advantages

1. **Adaptive:** Discovers relevant fields dynamically via ReAct exploration
2. **Semantic:** LLM generates contextual evaluation prompts (not hardcoded rules)
3. **Parallel:** Both Phase 2 expansion and Phase 3 execution run concurrently
4. **Robust:** Score parsing handles diverse LLM output formats
5. **Observable:** Multi-level debug mode for development and troubleshooting
