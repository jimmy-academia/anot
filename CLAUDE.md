# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based LLM evaluation framework comparing prompting methodologies on a restaurant recommendation task. The system evaluates LLMs against a dataset with ground-truth labels for three user personas.

## Commands

**IMPORTANT: Always use `.venv/bin/python` or activate the virtual environment first!**

### Run Evaluation
```bash
# ALWAYS use the virtual environment
source .venv/bin/activate
# OR prefix commands with .venv/bin/python

# Development mode (default): creates results/dev/{NNN}_{run-name}/
.venv/bin/python main.py --method cot --run-name baseline
python main.py --method anot --run-name experiment1

# Benchmark mode: set BENCHMARK_MODE=True in utils/arguments.py
# Creates results/benchmarks/{run-name}/ (tracked in git)

# Custom data paths
python main.py --method anot --data data/processed/complex_data.jsonl --run-name complex

# With pre-generated attacks
python main.py --method anot --attack typo_10 --run-name robustness

# Test with dummy method
python main.py --method dummy --limit 5 -v
```

### Generate Attacked Data
```bash
# Pre-generate attacked datasets (one-time)
python data/scripts/generate_attacks.py data/processed/real_data.jsonl
# Creates: data/attacked/typo_10.jsonl, data/attacked/inject_override.jsonl, etc.
```

### Environment Setup
```bash
# IMPORTANT: Always activate the virtual environment first
source .venv/bin/activate

# NOTE: Do not run pip install commands. If a package is missing, notify the user
# and let them decide whether to install it.

# API key: llm.py auto-loads from ../.openaiapi (no manual export needed)
# Or set manually:
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional LLM configuration
export LLM_PROVIDER="openai"  # or "anthropic" or "local"
export LLM_MODEL="gpt-4o-mini"

# Verbose terminal output (default: on, use --no-verbose to disable)
python main.py --method anot --no-verbose

# Structured logs written to {run_dir}/:
#   results_{n}.jsonl   - predictions + per-request usage
#   usage.jsonl         - consolidated usage across runs
#   anot_trace.jsonl    - ANoT phase-level structured trace
#   debug.log           - ANoT debug (always-on, file-only, overwrites each run)
#   config.json         - run configuration
#
# ANoT debug.log: Full LLM prompts/responses, phase traces, timestamps.
# No env var needed - always written when run_dir exists.
# See doc/logging.md for full schema details
```

## Architecture

### Core Files

- **main.py** - Entry point: parses args, sets up experiment, delegates to run/.

- **run/** - Evaluation orchestration package:
  - `orchestrate.py` - `run_single()`, `run_evaluation_loop()`
  - `evaluate.py` - `evaluate_ranking()`, `compute_multi_k_stats()`
  - `scaling.py` - `run_scaling_experiment()`
  - `shuffle.py` - Shuffle utilities for position bias mitigation
  - `io.py` - Result loading/saving

- **methods/anot/** - Adaptive Network of Thought package:
  - `core.py` - Main `AdaptiveNetworkOfThought` class with 3 phases
  - `helpers.py` - DAG building, formatting utilities
  - `tools.py` - Phase 2 LWT manipulation tools
  - `prompts.py` - LLM prompt constants

- **utils/experiment.py** - `ExperimentManager` class for dev/benchmark mode directory handling.

- **utils/llm.py** - Unified LLM API wrapper. Supports OpenAI, Anthropic, and local endpoints.

- **methods/cot.py** - Chain-of-Thought using few-shot prompting.

- **attack.py** - Attack functions (typo, injection, fake_review) and configs.

### Directory Structure

```
data/
├── raw/           # Raw Yelp data
├── processed/     # Generated datasets (real_data.jsonl, complex_data.jsonl)
├── attacked/      # Pre-generated attacked datasets
├── requests/      # User persona definitions
└── scripts/       # Data generation scripts

results/
├── dev/           # Development runs (gitignored)
│   ├── 001_baseline/
│   └── 002_experiment/
└── benchmarks/    # Benchmark runs (tracked in git)
    └── final_run/

run/               # Evaluation orchestration package
├── orchestrate.py # run_single, run_evaluation_loop
├── evaluate.py    # evaluate_ranking, stats computation
├── scaling.py     # Scaling experiment
├── shuffle.py     # Shuffle utilities
└── io.py          # Result I/O

methods/           # Evaluation methods
├── anot/          # ANoT package (core.py, helpers.py, tools.py, prompts.py)
├── cot.py         # Chain-of-Thought
├── listwise.py    # Listwise reranking
├── weaver.py      # SQL+LLM hybrid
└── ...

utils/             # Utility modules
doc/               # Implementation documentation (not for main paper)
```

**Note**: Documentation in `doc/` describes implementation details for code maintenance. These are not intended for the main research paper.

### Method Interface

All methods implement:
```python
def method(query, context: str) -> int
    # returns: -1 (not recommend), 0 (neutral), 1 (recommend)
```

### Variable Substitution (methods/anot/)

ANoT uses path-based variable substitution for data access:

| Variable | Maps to | Description |
|----------|---------|-------------|
| `{(context)}` | items dict | Restaurant data (1-indexed) |
| `{(input)}` / `{(items)}` | items dict | Same as context |
| `{(query)}` | user_query | User's request text |
| `{(step_id)}` | cache | Previous step output |

**Path-based access**: Access single leaf values to minimize tokens
```
# Access item 1's GoodForKids attribute
{(context)}[1][attributes][GoodForKids] → True

# Access nested attribute
{(context)}[2][attributes][Ambience][hipster] → False

# Reference previous step
{(c1)} → "[1, 5, 10]"
```

### Key Design Patterns

1. **Leakage Prevention**: `final_answers` and `condition_satisfy` never passed to LLM.

2. **Variable Substitution**: `{(var)}[key][index]` for nested access in scripts.

3. **Dynamic Script Generation** (methods/anot/): LLM generates execution plan at runtime.

### User Request Personas (R0, R1, R2)

- **R0**: Quiet dining, comfortable seating, budget-conscious
- **R1**: Allergy-conscious, needs clear ingredient labeling
- **R2**: Chicago tourist seeking authentic local experience

## Context Truncation (Pack-to-Budget)

String-mode methods (cot, ps, listwise, etc.) use dynamic pack-to-budget truncation to fit context within model limits.

### Policy (Fixed)

- **Priority**: Metadata first, then reviews
- **Order**: Restaurants in shuffled order, reviews in original order
- **Selection**: First N reviews that fit (no semantic ranking)
- **Budget**: Model-specific input token limit

### Token Limits

Defined in `utils/llm.py`:
- `MODEL_INPUT_LIMITS`: Fixed input budgets (e.g., gpt-5-nano → 270k)
- `MODEL_CONTEXT_LIMITS`: Context windows for formula-based calculation
- `get_token_budget(model)`: Returns input token budget

### Implementation

- `data/loader.py:format_ranking_query_packed()` - Two-pass packing:
  1. Include all restaurants with metadata (ensures fair evaluation)
  2. Add reviews round-robin until budget exhausted
- Uses `tiktoken` for accurate token counting

### Coverage Stats

Each result includes coverage stats when truncation is applied:
```json
{
  "coverage": {
    "restaurants": 50,
    "reviews_included": 127,
    "reviews_total": 500,
    "tokens_used": 245000
  }
}
```

### Which Methods Use Truncation

- **String mode** (truncated): cot, ps, plan_act, listwise, etc.
- **Dict mode** (no truncation): anot, weaver, react - they access data selectively

Defined in `data/loader.py:DICT_MODE_METHODS`.

## Data Preprocessing

The data loader (`data/loader.py`) performs preprocessing during `load_dataset()`:

### Field Stripping

Bloated fields are automatically removed to reduce token usage (~26% savings):

**Review-level**: `review_id`, `business_id`, `user_id`
**User-level**: `friends` (650+ bytes each), `user_id`, `elite`

Defined in `STRIP_REVIEW_FIELDS` and `STRIP_USER_FIELDS`.

### G09/G10 Social Data Synthesis

Social filter requests (G09: 1-hop friends, G10: 2-hop friends-of-friends) require synthetic social data in reviews. The loader applies precalculated mappings from `user_mapping.json`:

```json
{
  "user_names": {"USER_01": "Alice", "USER_02": "Bob", ...},
  "friend_graph": {"USER_01": ["USER_02", "USER_03"], ...},
  "restaurant_reviews": {
    "0": [["USER_01", "cozy"], ["USER_02", "quiet"]],
    ...
  }
}
```

For matching reviews (restaurant + pattern), the loader sets:
- `user.name` → synthetic friend name (e.g., "Alice")
- `user.friends` → translated friend list (e.g., ["Bob", "Carol"])

This enables:
- G09: "My friend Alice mentioned 'cozy'" → find review where name="Alice"
- G10: "Bob or his friends mentioned 'recommend'" → find review where name is Bob OR name's friends include Bob

## Attack Implementation

**Status**: Core infrastructure done, testing in progress. See `doc/internal/attack_plan.md` for full plan.

**Goal**: Test robustness - attacks should cause CoT to fail while ANoT resists.

### What's Done
- ✅ `attack.py` - Full implementation (typo, injection ×4, fake_review, sarcastic, heterogeneity)
- ✅ `run/evaluate.py:91-97` - Per-request attack application (protects gold item)
- ✅ Attack config stored in `config.json` for reproducibility

### What's In Progress
- ⚠️ Testing: Previous tests used only 2 requests (inconclusive)
- ❌ Defense testing: `--defense` flag exists but untested

### Available Attacks
```bash
# Noise attacks
python main.py --method cot --attack typo_10    # 10% word typos
python main.py --method cot --attack typo_20    # 20% word typos

# Injection attacks (target non-gold items)
python main.py --method cot --attack inject_override      # "IGNORE INSTRUCTIONS"
python main.py --method cot --attack inject_fake_sys      # Fake system messages
python main.py --method cot --attack inject_hidden        # Hidden instructions
python main.py --method cot --attack inject_manipulation  # Authority/FOMO

# Fake review attacks
python main.py --method cot --attack fake_positive   # Add glowing review
python main.py --method cot --attack fake_negative   # Add terrible review
python main.py --method cot --attack sarcastic_all   # Misleading sentiment
```

### Key Constraint
**NEVER modify gold items** - all attacks target non-gold items only.
