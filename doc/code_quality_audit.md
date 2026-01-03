# Code Quality Audit Report

**Date**: 2026-01-03
**Overall Code Health**: 7.5/10 (improved from 6.5)

---

## Completed Fixes

### Low Risk (All Done)
- [x] Remove unused imports from `methods/shared.py` (os, json, datetime, Path)
- [x] Delete dead function `_get_next_benchmark_run()` from `utils/experiment.py`
- [x] Remove unused `args.selection_name` from `utils/arguments.py`
- [x] Pre-compile 14 regex patterns in `methods/anot.py`
- [x] Consolidate duplicate `setup_logging()` - removed from `utils/logger.py`

### Medium Risk (Mostly Done)
- [x] Extract usage recording helper `_record_usage()` in `utils/llm.py`
- [x] Extract progress display helper `_run_with_progress()` in `run.py`
- [x] Reviewed prompts: `SYSTEM_PROMPT_RANKING` is intentionally different per method (not duplication)

### Remaining Medium Risk (Optional)
- [ ] Split `run.py` (850+ lines) into modules
- [ ] Split `methods/anot.py` (1000+ lines) into modules
- [ ] Break up long functions (`run_scaling_experiment`, `phase1_explore`)

---

## HIGH RISK FIXES (Behavioral changes, needs careful review)

These changes affect runtime behavior and require thorough testing.

### 1. Add Cycle Detection in `build_execution_layers()` - CRITICAL
- **Location**: `methods/shared.py:80-97`
- **Risk**: Infinite loop if LLM generates circular dependencies
- **Fix**: Add visited set, detect cycles, raise `ValueError`

### 2. Fix Race Condition in `_update_display()` - CRITICAL
- **Location**: `anot.py:440-466`
- **Risk**: Incorrect completion count in parallel execution
- **Fix**: Move completion check inside lock scope

### 3. Validate LLM-Generated Code Before eval() - CRITICAL
- **Location**: `weaver.py:227`
- **Risk**: Code injection / unexpected behavior
- **Fix**: Whitelist allowed operations, sandbox execution

### 4. Improve Error Handling (Silent Failures)
- **Location**: `anot.py:786, 1045`
- **Current**: `except Exception: output = "0"` - swallows all errors
- **Risk**: Can't distinguish between "result is 0" and "execution failed"
- **Fix**: Log exception, return error indicator, or raise custom exception

### 5. Replace Global State with Dependency Injection
- **Files**: `utils/llm.py`, `utils/usage.py`
- **Risk**: Breaks existing initialization patterns
- **Fix**: Create `LLMClientManager` class, pass as parameter

### 6. Widen Trace Lock Scope
- **Location**: `anot.py:341-362`
- **Risk**: Data loss during async operations
- **Fix**: Hold lock for entire trace update, not just dict access

---

## Summary

| Risk Level | Original | Completed | Remaining |
|------------|----------|-----------|-----------|
| Low | 5 items | 5 | 0 |
| Medium | 4 items | 3 | 1 (optional file splits) |
| High | 6 items | 0 | 6 |

---

## Files Modified

### Completed
- `methods/shared.py` - removed unused imports
- `utils/experiment.py` - deleted dead function
- `utils/arguments.py` - removed unused variable
- `utils/logger.py` - removed duplicate setup_logging, added reference to main.py
- `methods/anot.py` - pre-compiled 14 regex patterns
- `utils/llm.py` - extracted `_record_usage()` helper
- `run.py` - extracted `_run_with_progress()` helper

### Pending (High Risk)
- `methods/shared.py:80-97` - add cycle detection
- `methods/anot.py:440-466` - fix race condition
- `methods/weaver.py:227` - validate eval input
- `methods/anot.py:786,1045` - improve error handling
