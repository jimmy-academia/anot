# General ANoT Exploration

Task-agnostic Adaptive Network of Thought for semantic reasoning tasks.

## Architecture

```
explore/
├── general_anot/           # Main framework
│   ├── phase1.py           # Formula -> Formula Seed (LLM compilation)
│   ├── phase2.py           # Formula Seed interpreter (execution)
│   ├── eval.py             # Full evaluation with AUPRC scoring
│   ├── FORMULA_SEED_SPEC.md  # Specification documentation
│   └── DESIGN.md           # Design principles
│
├── baselines/              # Baseline methods for comparison
│   ├── direct_llm_v1.py    # Direct LLM (V1 formula)
│   ├── direct_llm_v2.py    # Direct LLM (V2 formula)
│   └── cot.py              # Chain of Thought
│
├── scoring/                # Evaluation utilities
│   ├── auprc.py            # Ordinal AUPRC scoring
│   └── ground_truth.py     # Deterministic GT computation
│
├── tasks/                  # Task definitions
│   └── g1_allergy.py       # Peanut allergy safety (G1a, G1a-v2)
│
├── data/                   # Datasets
│   ├── dataset_K200.jsonl  # 100 restaurants, 13K+ reviews
│   └── semantic_gt/        # Stored per-review LLM judgments
│
├── results/                # Evaluation results
│   ├── general_anot_eval/  # Current eval results
│   └── phase1_v2/          # Current Formula Seed
│
├── tools/                  # Data preparation tools
│
├── doc/                    # Additional documentation
│
└── archive/                # Archived/outdated code
```

## Quick Start

```bash
# Run full evaluation (100 restaurants, parallel)
python -m explore.general_anot.eval

# Or from explore directory
cd explore
python -m general_anot.eval
```

## Performance (G1a-v2 Task)

| Metric | Value |
|--------|-------|
| Ordinal AUPRC | 0.799 |
| Primitive Accuracy | 0.765 |
| **Adjusted AUPRC** | **0.612** |
| Verdict Accuracy | 87% |
| Time (100 restaurants) | 87s |

## Key Concepts

### Formula Seed

The Formula Seed is the output of Phase 1 - a complete, executable specification that Phase 2 interprets. It contains:

1. **Filtering**: Keywords to identify relevant reviews
2. **Extraction**: Semantic signals to extract from each review (with full definitions)
3. **Aggregation**: How to combine extractions (count, sum, max, min)
4. **Computation**: Formulas to compute final results

### Adjusted AUPRC

The evaluation metric that penalizes correct conclusions from wrong reasoning:

```
Adjusted AUPRC = Ordinal AUPRC × Primitive Accuracy
```

- **Ordinal AUPRC**: How well the risk score orders restaurants by true risk class
- **Primitive Accuracy**: How accurately intermediate values match ground truth

## Usage

```python
from explore.general_anot import generate_formula_seed, FormulaSeedInterpreter

# Phase 1: Compile task formula to executable seed
seed = await generate_formula_seed(task_prompt, "task_name")

# Phase 2: Execute seed on restaurant data
interpreter = FormulaSeedInterpreter(seed)
result = await interpreter.execute(reviews, restaurant_context)

# Result contains FINAL_RISK_SCORE, VERDICT, and all intermediate values
print(result["VERDICT"])  # "Low Risk", "High Risk", or "Critical Risk"
```

## Baselines

Compare against baseline methods:

```bash
# Direct LLM (V2 formula)
python -m explore.baselines.direct_llm_v2 --limit 10

# Chain of Thought
python -m explore.baselines.cot --limit 10
```
