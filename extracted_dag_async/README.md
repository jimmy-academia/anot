# Extracted DAG Async Code (For Review)

This folder contains code extracted from git history for review purposes.

## Source Commits
- `8e4ab7c^` - Hierarchical parallel Phase 2 (before deletion on Jan 8, 2026)
- `fda04fc` - Original knot.py with parallel async execution (Dec 26, 2025)

## Key Files

### Hierarchical Agent System (from 8e4ab7c^)
- **`phase2_hierarchical.py`** - 3-level ReAct agent hierarchy (Main → Item → Review)
- **`core_with_hierarchical.py`** - ANoT core with hierarchical mode integration
- **`helpers.py`** - Contains `build_execution_layers()` for topological DAG analysis
- **`tools.py`** - LWT manipulation tools for Phase 2
- **`prompts.py`** - LLM prompt constants
- **`__init__.py`** - Package exports

### Original Parallel Async (from fda04fc)
- **`knot_original.py`** - Original parallel execution with `execute_script_parallel()`
- **`llm_async.py`** - `call_llm_async()` for OpenAI/Anthropic async API calls

## Architecture Overview

### Hierarchical Agent System
```
Main Agent (depth 0): hard filtering → spawn item agents
  └── Item Agent (depth 1): metadata checks → spawn review agents
        └── Review Agent (depth 2): text search (leaf)
```

### DAG Parallel Execution
```python
# Build execution layers (topological sort)
layers = build_execution_layers(steps)

# Execute each layer in parallel
for layer in layers:
    results = await asyncio.gather(*[run_step(idx, instr) for idx, instr in layer])
```

## Key Functions

### `build_execution_layers(steps)` in helpers.py
Groups LWT steps into layers based on dependency analysis. Steps in the same layer can run in parallel.

### `execute_script_parallel()` in knot_original.py
Async execution of LWT script with DAG-based parallelization.

### `run_hierarchical_phase2()` in phase2_hierarchical.py
Entry point for hierarchical agent execution. Returns `List[Tuple[str, str]]` of (step_id, prompt) pairs.

### `call_llm_async()` in llm_async.py
Async wrapper for OpenAI/Anthropic API calls using `AsyncOpenAI()` and `AsyncAnthropic()`.

## DO NOT
- Import these files directly into the main codebase
- These are for **REVIEW ONLY**

## To Restore
If you want to restore this functionality:
1. Copy `phase2_hierarchical.py` to `methods/anot/`
2. Add hierarchical integration to `methods/anot/core.py`
3. Add `--hierarchical` CLI flag to `utils/arguments.py`
