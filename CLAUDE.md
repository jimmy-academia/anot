# CLAUDE.md

LLM evaluation framework comparing prompting methods on restaurant recommendations.

## Important Rules for Claude

- **NEVER use `rm -rf` on benchmark results** - Always prompt the user to delete files manually
- **Use `--dev` flag for development testing** - Results go to `results/dev/` (gitignored)
- Only commit benchmark results when explicitly requested

## Quick Reference

```bash
# Always use virtual environment
source .venv/bin/activate

# Run evaluation
python main.py --method anot --candidates 50
python main.py --method cot --candidates 10 --attack typo_10

# Scaling experiment (default, no --candidates)
python main.py --method anot

# Dev mode (results/dev/)
python main.py --method anot --candidates 50 --dev

# Attack sweep
python main.py --method cot --attack all --candidates 10
```

**Key locations:**
- Add method: `methods/newmethod.py` + `methods/__init__.py` (METHOD_REGISTRY)
- Add attack: `attack.py` (ATTACK_CONFIGS)
- Change models: `utils/llm.py` (MODEL_CONFIG)
- Modify evaluation: `run/evaluate.py`

## Method System

### BaseMethod Class

All methods inherit from `BaseMethod` (`methods/base.py`):

```python
class BaseMethod(ABC):
    name: str = "base"

    def __init__(self, run_dir: str = None, defense: bool = False, verbose: bool = True, **kwargs):
        ...

    @abstractmethod
    def evaluate(self, query: Any, context: str) -> int:
        """Single item evaluation.
        Returns: 1 (recommend), 0 (neutral), -1 (not recommend)
        """

    def evaluate_ranking(self, query: str, context: str, k: int = 1) -> str:
        """Ranking task. Returns comma-separated indices e.g. '3, 1, 5'"""
        return "1"  # Default
```

### Method Registry

Methods are registered in `methods/__init__.py`:

```python
METHOD_REGISTRY = {
    "cot": (ChainOfThought, True),      # (class, supports_defense)
    "ps": (PlanAndSolve, False),
    "plan_act": (PlanAndAct, True),
    "listwise": (ListwiseRanker, True),
    "weaver": (Weaver, True),
    "anot": (AdaptiveNetworkOfThought, True),
    "react": (ReAct, False),
    ...  # 17 total methods
}

# Factory function
get_method(name, run_dir, defense, verbose) -> BaseMethod
```

**Defense-enabled methods** (5): cot, plan_act, listwise, weaver, anot

### Adding a New Method

1. Create `methods/mymethod.py`:
```python
from .base import BaseMethod

class MyMethod(BaseMethod):
    name = "mymethod"

    def evaluate(self, query, context: str) -> int:
        ...

    def evaluate_ranking(self, query: str, context: str, k: int = 1) -> str:
        ...
```

2. Register in `methods/__init__.py`:
```python
from .mymethod import MyMethod
METHOD_REGISTRY["mymethod"] = (MyMethod, False)  # (class, supports_defense)
```

## Data Modes

### String vs Dict Mode

```python
# data/loader.py
DICT_MODE_METHODS = {"anot", "weaver", "react"}
```

| Mode | Methods | Context Type | Truncation |
|------|---------|--------------|------------|
| **String** | cot, ps, listwise, etc. | Pre-formatted text | Yes (pack-to-budget) |
| **Dict** | anot, weaver, react | Raw dict | No (selective access) |

Mode is determined in `run/orchestrate.py:42`:
```python
eval_mode = "dict" if args.method in DICT_MODE_METHODS else "string"
```

### Token Budget

For string-mode methods, context is truncated to fit token budget.

**Calculation** (`utils/llm.py:get_token_budget()`):
1. If model in `MODEL_INPUT_LIMITS`: use fixed limit
2. Else: `context_window - 2000 (output) - 5% (safety)`

```python
MODEL_INPUT_LIMITS = {"gpt-5-nano": 270000}
MODEL_CONTEXT_LIMITS = {"gpt-4o": 128000, "claude-3-5-sonnet-20241022": 200000, ...}
```

**Pack-to-budget algorithm** (`data/loader.py:format_ranking_query_packed()`):
1. Pass 1: Include all restaurants with metadata
2. Pass 2: Add reviews round-robin until budget exhausted

## Evaluation Flow

```
main.py
  -> parse_args()                    [utils/arguments.py]
  -> config_llm(args)                [utils/llm.py]
  -> ExperimentManager()             [utils/experiment.py]
  |
  +-> run_scaling_experiment()       [run/scaling.py] (default, no --candidates)
  +-> run_single()                   [run/orchestrate.py] (with --candidates)
      -> load_dataset()              [data/loader.py]
      -> get_method()                [methods/__init__.py]
      -> run_evaluation_loop()       [run/orchestrate.py]
         -> evaluate_ranking()       [run/evaluate.py]
            -> apply_shuffle()       [run/shuffle.py]
            -> format_context()      (string/dict based on DICT_MODE_METHODS)
            -> method.evaluate_ranking()
            -> parse_indices()       [utils/parsing.py]
            -> unmap_predictions()   (reverse shuffle)
```

**Special case**: ANoT accepts `request_id` parameter, detected via `inspect.signature()` in `run/evaluate.py:134-137`.

## ANoT Package

`methods/anot/` contains the Adaptive Network of Thought implementation:

- `core.py` - Main `AdaptiveNetworkOfThought` class (3-phase architecture)
- `helpers.py` - DAG building, dependency analysis
- `tools.py` - LWT manipulation tools (`tool_read`, `tool_lwt_*`)
- `prompts.py` - LLM prompt constants

### Variable Substitution (ANoT only)

Path-based variable substitution for selective data access:

| Variable | Maps to | Description |
|----------|---------|-------------|
| `{(context)}` / `{(items)}` | items dict | Restaurant data (1-indexed) |
| `{(query)}` | user_query | User's request text |
| `{(step_id)}` | cache | Previous step output |

**Path syntax**:
```
{(context)}[1][attributes][GoodForKids]  -> True
{(context)}[2][reviews][0][text]         -> "Great place..."
{(c1)}                                   -> "[1, 5, 10]"
```

### Thread Safety

ANoT uses `threading.local()` for per-request context isolation during parallel execution.

### Output Files

- `anot_trace.jsonl` - Structured phase-level trace
- `debug.log` - Full LLM prompts/responses (always-on when run_dir exists)

## Attack System

13 attack types targeting non-gold items only:

```bash
# Noise
--attack typo_10           # 10% word typos
--attack typo_20           # 20% word typos

# Injection (4 types)
--attack inject_override   # "IGNORE INSTRUCTIONS"
--attack inject_fake_sys   # Fake system messages
--attack inject_hidden     # Hidden in positive language
--attack inject_manipulation  # Authority/FOMO

# Fake reviews
--attack fake_positive     # Glowing review
--attack fake_negative     # Terrible review

# Sarcastic (misleading sentiment)
--attack sarcastic_wifi    # WiFi-specific
--attack sarcastic_noise   # Noise-specific
--attack sarcastic_outdoor # Outdoor-specific
--attack sarcastic_all     # All attributes

# Length manipulation
--attack heterogeneity     # Requires --attack-target-len

# Batch modes
--attack all               # Run all attacks
--attack both              # Clean baseline + all attacks
```

**Key constraint**: Gold items are NEVER attacked (protected in `run/evaluate.py`).

**Per-request seeding**: Uses `hash(req_id) % (2**31)` for reproducibility.

## Configuration

### Global Flags

```python
# utils/arguments.py
PARALLEL_MODE = True    # Enable parallel API calls
BENCHMARK_MODE = True   # Use results/benchmarks/ (tracked in git)
```

Override via CLI: `--sequential`, `--dev`

### LLM Configuration

```python
# utils/llm.py
MODEL_CONFIG = {
    "planner": "gpt-5-nano",
    "worker": "gpt-5-nano",
    "default": "gpt-5-nano",
}

_config = {
    "temperature": 0.0,
    "max_tokens": 1024,
    "max_tokens_reasoning": 4096,
    "provider": "openai",
    "request_timeout": 90.0,
    "max_retries": 6,
}
```

**Rate limiting**: `init_rate_limiter(max_concurrent=200)` via semaphores.

**Retry**: Exponential backoff on 429/5xx errors (up to 6 retries).

### API Keys

Auto-loaded from `../.openaiapi` if env vars not set. Or:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Directory Structure

```
data/
├── {dataset}/         # e.g., philly_cafes/
│   ├── restaurants.jsonl
│   ├── reviews.jsonl
│   ├── requests.jsonl
│   ├── groundtruth.jsonl
│   └── user_mapping.json  # Optional: G09/G10 social synthesis
└── scripts/

results/
├── dev/               # Development runs (gitignored)
│   └── {NNN}_{run-name}/
└── benchmarks/        # Benchmark runs (tracked)
    └── {method}_{data}/{attack}/run_{N}/

methods/
├── __init__.py        # METHOD_REGISTRY, get_method()
├── base.py            # BaseMethod abstract class
├── anot/              # ANoT package
│   ├── core.py
│   ├── helpers.py
│   ├── tools.py
│   └── prompts.py
├── cot.py
├── listwise.py
└── ...                # 17 total methods

run/
├── orchestrate.py     # run_single(), run_evaluation_loop()
├── evaluate.py        # evaluate_ranking(), stats computation
├── scaling.py         # run_scaling_experiment()
├── shuffle.py         # Position bias mitigation
└── io.py              # Result I/O

utils/
├── arguments.py       # CLI parsing, PARALLEL_MODE, BENCHMARK_MODE
├── experiment.py      # ExperimentManager
├── llm.py             # LLM wrapper, MODEL_CONFIG, token limits
├── parsing.py         # parse_indices(), parse_final_answer()
└── usage.py           # Token tracking
```

## Output Files

Each run produces in `{run_dir}/`:
- `config.json` - Run configuration
- `results_{n_candidates}.jsonl` - Predictions + per-request usage
- `usage.jsonl` - Consolidated token usage
- `debug.log` - LLM traces (method-specific)
- `anot_trace.jsonl` - ANoT phase traces (if ANoT method)

**Coverage stats** (string-mode only):
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

## CLI Arguments

**Data**: `--data`, `--run-name`, `--limit`, `--run`, `--force`, `--review-limit`, `--candidates`

**Method**: `--method` (cot, ps, plan_act, listwise, weaver, anot, react, dummy)

**Attack**: `--attack`, `--seed`, `--defense`, `--attack-restaurants`, `--attack-reviews`, `--attack-target-len`

**LLM**: `--provider`, `--model`, `--temperature`, `--max-tokens`, `--max-tokens-reasoning`, `--base-url`

**Evaluation**: `--k` (Hits@K), `--shuffle` (none/middle/random)

**Execution**: `--max-concurrent`, `--sequential`, `--auto`, `--dev`

**Output**: `--verbose`/`-v` (default: True), `--full`

## Data Preprocessing

### Field Stripping (~26% token savings)

```python
# data/loader.py
STRIP_USER_FIELDS = {'friends', 'user_id'}
STRIP_REVIEW_FIELDS = {'review_id', 'business_id', 'user_id'}
```

### G09/G10 Social Synthesis

Optional `user_mapping.json` enables friend-based filtering requests. If missing, dataset works without social features.
