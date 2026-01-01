# Codebase Reorganization Plan

## Overview
Reorganize the xnot LLM evaluation framework to improve maintainability, reduce duplication, and clean up the data directory.

---

## Phase 0: Document Organization

### Current Issues
- `notes.md` is incomplete/abandoned (29 lines, references broken links)
- No index or README explaining doc structure
- `auto_commit.md` is tool docs, doesn't belong in doc/
- Paper LaTeX files have no main.tex to compile
- Overlap between `experiment_plan.md` and `baseline_todo.md`

### 0.1 Save This Plan
- [x] Copy this reorganization plan to `doc/reorganization_plan.md`

### 0.2 Create doc/README.md
Create index explaining document purposes.

### 0.3 Clean Up
- [ ] Delete or complete `notes.md` (currently abandoned)
- [ ] Move `auto_commit.md` to `scripts/` (it's tool documentation)
- [ ] Delete `.DS_Store`

### 0.4 Paper Structure
- [ ] Create `paper/main.tex` if paper is meant to compile
- [ ] Or add note in README that paper sections are drafts

---

## Phase 1: Deletions (Safe, No Breaking Changes)

### 1.1 Delete Dead Code
- [ ] Delete `/past_ref/` directory (entire tree)
- [ ] Delete `/methods/past_ref/` directory (anot.py, anot_v2.py)
- [ ] Delete `/methods/anot_origin.py`
- [ ] Update `/methods/__init__.py` to remove anot_origin references

### 1.2 Rename anot_v3 to anot
- [ ] Rename `methods/anot_v3.py` → `methods/anot.py`
- [ ] Update `methods/__init__.py` imports

---

## Phase 2: Consolidate Logging (Low Risk)

### Current State
- `utils/logger.py` (32 lines) - re-exports
- `utils/simple_logger.py` (105 lines) - Rich console
- `utils/debug_logger.py` (201 lines) - experiment JSONL

### Changes
- [ ] Rename `simple_logger.py` → `console.py`
- [ ] Rename `debug_logger.py` → `experiment_logger.py`
- [ ] Update `logger.py` to be unified facade with clear exports
- [ ] Update all import statements across codebase

---

## Phase 3: Extract Shared Code in methods/ (Medium Risk)

### 3.1 Defense Prompt Mixin
Create `methods/prompts/defense_mixin.py`:
```python
class DefensePromptMixin:
    SYSTEM_PROMPT_NORMAL: str = ""
    SYSTEM_PROMPT_DEFENSE: str = ""

    def _get_system_prompt(self, ranking: bool = False) -> str:
        # Centralized defense prompt logic
```

Files to refactor (remove duplicate `_get_system_prompt()`):
- [ ] `cot.py`
- [ ] `react.py`
- [ ] `decomp.py`
- [ ] `listwise.py`
- [ ] `finegrained.py`
- [ ] `prp.py`
- [ ] `pot.py`

### 3.2 Ranking Mixin
Create `methods/ranking_mixin.py`:
```python
class RankingMixin:
    def _build_ranking_prompt(self, query, context, k) -> str: ...
    def _parse_indices(self, response, max_index, k) -> List[int]: ...
    def evaluate_ranking(self, query, context, k) -> str: ...
```

Methods with standard ranking patterns to inherit mixin:
- `l2m.py`, `ps.py`, `selfask.py`, `cotsc.py`, `listwise.py`

Methods with custom ranking (keep custom impl):
- `anot.py`, `finegrained.py`, `prp.py`, `rankgpt.py`

---

## Phase 4: Data Directory Organization

### Current Issues
- Flat structure in `data/yelp/` - cache, processed, and output files all mixed
- Legacy files: `requests_1.json` (superseded by .jsonl), `.backup` files
- Unclear files: `edits_1.jsonl`, `notes_1`, `judgments_cache.jsonl`
- No documentation of data pipeline or file purposes
- Two curation scripts (`yelp_curation.py` + `auto_curate.py`) with overlapping purpose

### 4.1 Clean Up data/yelp/
- [ ] Delete legacy `requests_1.json` (keep only .jsonl version)
- [ ] Move `.backup` files to `data/yelp/archive/` or delete
- [ ] Clarify or delete unclear files (`edits_1.jsonl`, `notes_1`)

### 4.2 Organize by Selection
Group related files per selection:
```
data/yelp/
├── raw/                          # Raw Yelp dataset (unchanged)
├── selections/                   # NEW: Selection definitions
│   ├── selection_1.jsonl
│   ├── selection_2.jsonl
│   └── selection_3.jsonl
├── processed/                    # NEW: Processed outputs
│   ├── 1/                        # Selection 1 outputs
│   │   ├── reviews_cache.jsonl
│   │   ├── restaurants_cache.jsonl
│   │   ├── rev_selection.jsonl
│   │   ├── requests.jsonl
│   │   └── groundtruth.jsonl
│   ├── 2/
│   └── 3/
├── archive/                      # NEW: Legacy/backup files
└── meta_log.json
```

### 4.3 Script Organization
- [ ] Consolidate `yelp_curation.py` and `auto_curate.py` into unified script
- [ ] Rename scripts for clarity:
  - `yelp_precompute_groundtruth.py` → `compute_groundtruth.py`
  - `yelp_review_sampler.py` → `sample_reviews.py`
  - `yelp_requests.py` → `generate_requests.py`
  - `yelp_curation.py` → `curate.py`
- [ ] Add `data/scripts/README.md` documenting the pipeline

### 4.4 Update loader.py
- [ ] Update `data/loader.py` to use new paths (with backward compatibility)

---

## Phase 5: Benchmark Storage & Results Management

### Current Issues
- No master index of all benchmark runs (scattered across 99 directories)
- Many runs missing `stats` in config.json (incomplete tracking)
- No multi-method comparison utilities
- Dev results accumulate without cleanup (14+ directories)
- Summary files duplicated at multiple levels
- No run health/completion validation

### 5.1 Add Results Manifest
Create `results/benchmarks/manifest.json`:
```json
{
  "runs": [
    {
      "id": "cot_yelp/clean/selection_1_run_1",
      "method": "cot",
      "data": "yelp",
      "attack": "clean",
      "selection": 1,
      "run": 1,
      "status": "complete",
      "created": "2024-01-15T10:30:00Z",
      "stats": { ... }
    }
  ]
}
```
- [ ] Create script to generate manifest from existing runs
- [ ] Update `ExperimentManager` to append to manifest on run completion
- [ ] Add `--list-runs` command to show all benchmarks

### 5.2 Comparison Utilities
Create `utils/compare.py`:
- [ ] `compare_methods(methods, selection)` - table comparing methods on same data
- [ ] `compare_attacks(method, attacks)` - table comparing attack robustness
- [ ] `export_comparison(format='markdown'|'csv')` - export comparison tables

### 5.3 Dev Results Cleanup
- [ ] Add `--cleanup-dev` flag to main.py to archive/delete old dev runs
- [ ] Add `--keep-last N` option to keep only N most recent dev runs
- [ ] Move old dev runs to `results/dev/archive/` before deletion

### 5.4 Run Validation
- [ ] Add validation in `aggregate.py` to flag incomplete runs
- [ ] Add `--validate` command to check all benchmark run integrity
- [ ] Report missing stats, incomplete results, config mismatches

### 5.5 Consolidate Summary Files
- [ ] Remove duplicate summaries at multiple directory levels
- [ ] Single summary per method-data combination in `results/benchmarks/{method}_{data}/summary.json`
- [ ] Update `aggregate.py` to use consolidated location

---

## Critical Files

| File | Action |
|------|--------|
| `methods/__init__.py` | Remove anot_origin, update anot import |
| `methods/prompts/common.py` | Add defense_mixin.py |
| `utils/logger.py` | Consolidate logging |
| `data/loader.py` | Update for new data paths |
| `data/scripts/*.py` | Rename and consolidate |
| `utils/experiment.py` | Add manifest updates on run completion |
| `utils/aggregate.py` | Add validation, update summary locations |
| `utils/compare.py` | NEW: Comparison utilities |

---

## Execution Order

0. **Phase 0** - Document organization (first, saves plan to doc/)
1. **Phase 1** - Safe deletions, immediate cleanup
2. **Phase 2** - Logging consolidation (isolated change)
3. **Phase 3** - Extract mixins (reduces duplication)
4. **Phase 4** - Data directory organization
5. **Phase 5** - Benchmark storage & results management

Each phase should be committed separately for easy rollback.
