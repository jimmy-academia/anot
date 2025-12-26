# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based LLM evaluation framework comparing prompting methodologies on a restaurant recommendation task. The system evaluates LLMs against a dataset with ground-truth labels for three user personas.

## Commands

### Run Evaluation
```bash
python main.py --method cot --data data.jsonl --out results.jsonl
python main.py --method not --data data.jsonl --out results.jsonl
python main.py --method knot --data data.jsonl --out results.jsonl  # Dynamic script
python main.py --method knot --mode dict --data data.jsonl  # Dict indexing mode
python main.py --method dummy --limit 5  # Test with dummy method
```

### Environment Setup
```bash
# API key is stored in ../.openaiapi (parent directory)
export OPENAI_API_KEY=$(cat ../.openaiapi)

# Or for Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional LLM configuration (llm.py)
export LLM_PROVIDER="openai"  # or "anthropic" or "local"
export LLM_MODEL="gpt-4o-mini"

# Debug output
export NOT_DEBUG=1   # for rnot.py
export KNOT_DEBUG=1  # for knot.py
```

## Architecture

### Core Files

- **main.py** - Evaluation harness with `--method` and `--mode` flags.

- **llm.py** - Unified LLM API wrapper. Supports OpenAI, Anthropic, and local endpoints.

- **cot.py** - Chain-of-Thought using few-shot prompting.

- **rnot.py** - Network-of-Thought with fixed 5-step pipeline.

- **knot.py** - Knowledge Network of Thought with dynamic 2-phase script generation:
  - Phase 1: Generate knowledge (step-by-step approach)
  - Phase 2: Generate executable script from knowledge
  - Supports `--mode string` (flatten input) or `--mode dict` (structured access)

- **data.jsonl** - Dataset with 9 Chicago restaurants and ground-truth labels.

### Method Interface

All methods implement:
```python
def method(query, context: str) -> int
    # returns: -1 (not recommend), 0 (neutral), 1 (recommend)
```

### Input Modes (knot.py)

**String mode** (default): Input is formatted text, LLM extracts info
```
(0)=LLM("Extract reviews from: {(input)}")
(1)=LLM("Analyze {(0)}[0]")
```

**Dict mode**: Input is dict, direct key/index access
```
(0)=LLM("Name is {(input)}[item_name]")
(1)=LLM("Review: {(input)}[item_data][0][review]")
```

### Key Design Patterns

1. **Leakage Prevention**: `final_answers` and `condition_satisfy` never passed to LLM.

2. **Variable Substitution**: `{(var)}[key][index]` for nested access in scripts.

3. **Dynamic Script Generation** (knot.py): LLM generates execution plan at runtime.

### User Request Personas (R0, R1, R2)

- **R0**: Quiet dining, comfortable seating, budget-conscious
- **R1**: Allergy-conscious, needs clear ingredient labeling
- **R2**: Chicago tourist seeking authentic local experience
