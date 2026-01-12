# Benchmark Results: Method Comparison

Task: G1a-v2 (Peanut Allergy Safety)
Dataset: 100 restaurants, 13K+ reviews
Date: January 2026

## Summary

| Method | Adjusted AUPRC | Range | Stability |
|--------|----------------|-------|-----------|
| **General ANoT** | **0.772 avg** | 0.765-0.781 | Highly stable |
| Direct LLM | 0.531 avg | 0.426-0.666 | Unstable |
| Chain of Thought | 0.489 avg | 0.256-0.607 | Very unstable |

---

## Detailed Results by Method

### General ANoT (3 runs)

| Metric | Run 1 | Run 2 | Run 3 | Range |
|--------|-------|-------|-------|-------|
| Ordinal AUPRC | 0.873 | 0.886 | 0.906 | 0.033 |
| Primitive Accuracy | 0.876 | 0.867 | 0.862 | 0.015 |
| **Adjusted AUPRC** | 0.765 | 0.769 | 0.781 | **0.016** |
| AUPRC (>=High) | 0.746 | 0.772 | 0.812 | 0.067 |
| AUPRC (>=Critical) | 1.000 | 1.000 | 1.000 | **0.000** |

Verdict distributions:
- Run 1: Low=97, High=1, Critical=2
- Run 2: Low=95, High=3, Critical=2
- Run 3: Low=96, High=2, Critical=2

### Chain of Thought (3 runs)

| Metric | Run 1 | Run 2 | Run 3 | Range |
|--------|-------|-------|-------|-------|
| Ordinal AUPRC | 0.743 | 0.325 | 0.771 | 0.445 |
| Primitive Accuracy | 0.815 | 0.787 | 0.787 | 0.027 |
| **Adjusted AUPRC** | 0.605 | 0.256 | 0.607 | **0.351** |
| AUPRC (>=High) | 0.652 | 0.390 | 0.541 | 0.262 |
| AUPRC (>=Critical) | 0.833 | 0.261 | 1.000 | **0.739** |

Verdict distributions:
- Run 1: Low=93, High=5, Critical=2
- Run 2: Low=93, High=5, Critical=2
- Run 3: Low=93, High=5, Critical=2

### Direct LLM (3 runs)

| Metric | Run 1 | Run 2 | Run 3 | Range |
|--------|-------|-------|-------|-------|
| Ordinal AUPRC | 0.825 | 0.626 | 0.521 | 0.304 |
| Primitive Accuracy | 0.807 | 0.800 | 0.817 | 0.017 |
| **Adjusted AUPRC** | 0.666 | 0.501 | 0.426 | **0.240** |
| AUPRC (>=High) | 0.651 | 0.252 | 0.709 | 0.457 |
| AUPRC (>=Critical) | 1.000 | 1.000 | 0.333 | **0.667** |

Verdict distributions:
- Run 1: Low=95, High=4, Critical=1
- Run 2: Low=95, High=4, Critical=1
- Run 3: Low=95, High=4, Critical=1

---

## Stability Comparison

| Method | Adjusted AUPRC Range | AUPRC (>=Critical) Range |
|--------|---------------------|--------------------------|
| **General ANoT** | **0.016** | **0.000** |
| Direct LLM | 0.240 | 0.667 |
| CoT | 0.351 | 0.739 |

General ANoT's range is:
- **22x smaller** than CoT for Adjusted AUPRC
- **15x smaller** than Direct LLM for Adjusted AUPRC
- **Perfect** Critical detection (0.000 variance)

---

## Ground Truth Distribution

| Verdict | Count |
|---------|-------|
| Low Risk | 95 |
| High Risk | 4 |
| Critical Risk | 1 |

---

## Why General ANoT is More Stable

| Factor | General ANoT | Baselines (CoT, Direct LLM) |
|--------|-------------|----------------------------|
| Filtering | Python (deterministic) | LLM (variable) |
| Extraction | LLM per review (isolated) | LLM entire context (coupled) |
| Aggregation | Python (deterministic) | LLM (variable) |
| Computation | Python (deterministic) | LLM (variable) |

Only Step 2 (extraction) uses LLM in General ANoT. Errors are isolated to individual reviews and don't cascade. Baselines use LLM for everything including arithmetic, causing high variance.

---

## Result Locations

```
explore/results/
├── G1a_cot_k200_20260110_221757/      # CoT Run 1
├── G1a_cot_k200_20260110_222734/      # CoT Run 2
├── G1a_cot_k200_20260110_223001/      # CoT Run 3
├── G1a-v2_k200_20260110_221622/       # Direct LLM Run 1
├── G1a-v2_k200_20260110_222233/       # Direct LLM Run 2
├── G1a-v2_k200_20260110_222520/       # Direct LLM Run 3
└── general_anot_eval/
    ├── 001_20260111_235459/           # General ANoT Run 1
    ├── 002_20260112_003551/           # General ANoT Run 2
    └── 003_20260112_003708/           # General ANoT Run 3
```
