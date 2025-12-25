# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based LLM evaluation framework comparing prompting methodologies (Chain-of-Thought vs Network-of-Thought) on a restaurant recommendation task. The system evaluates LLMs against a dataset with ground-truth labels for three user personas.

## Commands

### Run Evaluation
```bash
python test.py --data data.jsonl --out results.jsonl
python test.py --data data.jsonl --out results.jsonl --limit 5  # Limit items
python test.py --data data.jsonl --out results.jsonl --print_examples 3  # Show errors
```

### Test Individual Methods
```bash
# Chain-of-Thought
python cot.py --test
python cot.py --test --verbose
python cot.py --test --provider openai

# Network-of-Thought
NOT_DEBUG=1 python not.py
NOT_USE_DYNAMIC=1 python not.py  # Use dynamic script generation
```

### Environment Setup
```bash
# API key is stored in ../.openaiapi (parent directory)
export OPENAI_API_KEY=$(cat ../.openaiapi)

# Or for Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# NoT-specific configuration
export LLM_PROVIDER="openai"  # or "anthropic" or "local"
export LLM_MODEL="gpt-4o-mini"
```

## Architecture

### Core Files

- **test.py** - Evaluation harness that runs methods against the dataset and computes metrics (accuracy, confusion matrices). Currently uses `dummy_method` at line 576 - swap in `from cot import method` or `from not import method`.

- **cot.py** - Chain-of-Thought implementation using few-shot prompting with explicit reasoning examples. Exports `method(query, context) -> int` and `create_method()` factory.

- **not.py** - Network-of-Thought implementation with two modes:
  - `SimpleNetworkOfThought` (default): Fixed 5-step reasoning pipeline
  - `NetworkOfThought`: Dynamic script generation via planner LLM

- **data.jsonl** - Dataset with 9 Chicago restaurants, each with reviews and ground-truth labels for 3 user request types (R0/R1/R2).

### Method Interface

All methods must implement:
```python
def method(query: str, context: str) -> int
    # query: Restaurant info (name, location, reviews)
    # context: User request describing what they're looking for
    # returns: -1 (not recommend), 0 (neutral), 1 (recommend)
```

### Key Design Patterns

1. **Leakage Prevention**: The `final_answers` and `condition_satisfy` fields are never passed to the LLM - only used for evaluation comparison.

2. **Provider Abstraction**: Both methods support multiple LLM backends (Anthropic, OpenAI, local) with lazy-loaded dependencies.

3. **Variable Substitution** (not.py): Script steps reference previous outputs using `{(index)}` notation with optional list indexing `{(0)}[1]`.

### User Request Personas (R0, R1, R2)

- **R0**: Quiet dining, comfortable seating, budget-conscious
- **R1**: Allergy-conscious, needs clear ingredient labeling
- **R2**: Chicago tourist seeking authentic local experience
