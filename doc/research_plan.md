# Research Plan: ANoT (Adaptive Network of Thought)

## Problem Statement

LLMs fail on structured multi-source data due to:
1. Heterogeneity in user content
2. Adversarial content (fake reviews, injection)
3. Structure confusion (metadata vs text)

## Solution: ANoT

Split-context prompting that:
- Isolates evidence by source
- Generates validated execution scripts
- Adapts to detected heterogeneity/attacks

## Task Framing: Constraint-Satisfying Reranking

**Scenario:** Last-mile RAG

**Fixed Context:** 20 candidates × 20 reviews

**Goal:** Find the ONE candidate satisfying all constraints

---

## Specifications

### Data

| Spec | Value |
|------|-------|
| Domain | Yelp |
| Candidates | 20 restaurants |
| Reviews per candidate | 20 |
| Requests | 50 total |
| Ground truth | Exactly 1 valid per request |

### Request Groups

| Group | Description | Count |
|-------|-------------|-------|
| G01 | Simple metadata | 10 |
| G02 | Review text | 10 |
| G03 | Computed metadata (hours) | 10 |
| G04 | Social signals (elite, recency) | 10 |
| G05 | Nested logic (ceiling test) | 10 |

### Metrics

| Metric | Role |
|--------|------|
| **Hits@5** | Primary (paper tables) |
| Accuracy | Secondary (diagnosis) |

### Baselines (Champions Only)

| Category | Method |
|----------|--------|
| Reasoning | Plan-and-Solve (ps) |
| Ranking | Listwise |
| Structured | Weaver |
| Standard | Zero-shot CoT |

### Attacks (3 Categories)

| Category | Attacks |
|----------|---------|
| Noise | typo, verbose, duplicate |
| Injection | inject_override, inject_system |
| Deception | fake_positive, fake_negative, sarcastic |

---

## Build Order

### Phase 1: Documentation (Current)
- [x] Create directory structure
- [x] Write doc/README.md
- [x] Write doc/research_plan.md
- [ ] Write doc/evaluation_spec.md

### Phase 2: Data Pipeline
- [ ] Write scripts/curate.py
- [ ] Write scripts/generate_requests.py
- [ ] Write scripts/validate_gt.py
- [ ] Generate data files

### Phase 3: Code
*Port from oldsrc/ after data is ready*

### Phase 4: Experiments
*Run after code is ported*
