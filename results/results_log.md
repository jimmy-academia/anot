# Results Log

This document tracks all evaluation runs.

## Summary

| Run | Date | Method | Model | Data | Notes |
|-----|------|--------|-------|------|-------|
| 1_gpt5nano_baseline | 12-26 | knot | gpt-5-nano | real_data | Baseline run |
| 2_mixed_models_planner4omini_worker5nano | 12-26 | knot | planner=4o-mini, worker=5-nano | real_data | Mixed model config |
| 3_attack_eval | 12-26 | knot/cot | mixed | challenge_data | Adversarial attack testing |
| 4_verification | 12-25 | - | - | - | Result verification |

---

## Runs

### 1_gpt5nano_baseline
Baseline evaluation using gpt-5-nano for all LLM calls.

### 2_mixed_models_planner4omini_worker5nano
Mixed model configuration: gpt-4o-mini for planning, gpt-5-nano for execution.

### 3_attack_eval
Adversarial attack evaluation comparing knot vs cot robustness.

### 4_verification
Result verification and validation.
