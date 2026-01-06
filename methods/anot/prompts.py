#!/usr/bin/env python3
"""Prompt constants for ANoT phases - Strategy-Centric Design."""

from prompts.task_descriptions import RANKING_TASK_COMPACT

# Re-export for use in core.py
__all__ = ['SYSTEM_PROMPT', 'PHASE1_PROMPT', 'PHASE2_PROMPT', 'RANKING_TASK_COMPACT']

SYSTEM_PROMPT = "You follow instructions precisely. Output only what is requested."

# =============================================================================
# PHASE 1: Strategy Extraction (Schema-Aware, No Item Scanning)
# =============================================================================
# Phase 1 sees the SCHEMA (1-2 example items) to understand available fields,
# but does NOT try to find matching items. It outputs an execution STRATEGY.

PHASE1_PROMPT = """Analyze the user request and design an evaluation STRATEGY.

{task_description}

[SCHEMA - showing 1-2 example items so you know available fields]
{schema_compact}

[AVAILABLE FIELDS]
- attributes: Direct key-value pairs (GoodForKids, WiFi, DriveThru, CoatCheck, etc.)
- attributes.Ambience: Nested dict {{hipster:True, casual:True, upscale:False, ...}}
- attributes.GoodForMeal: Nested dict {{breakfast:True, lunch:False, brunch:True, ...}}
- hours: day=start-end format (e.g., Friday=12:0-22:0 means 12pm-10pm)
- reviews: Array of review objects with 'text' field containing reviewer comments

[TASK]
1. READ the user request. Extract ALL conditions mentioned.
2. CLASSIFY each condition by type:
   - [ATTR] Direct attribute lookup (e.g., GoodForKids=True, WiFi=free, DriveThru=True)
   - [AMBIENCE] Nested in Ambience dict (e.g., hipster vibe → Ambience.hipster=True)
   - [MEAL] Nested in GoodForMeal dict (e.g., good for brunch → GoodForMeal.brunch=True)
   - [HOURS] Operating hours check (e.g., open Friday after 9pm)
   - [REVIEW_TEXT] Keyword search in review text (e.g., "mentions 'work'" or "has reviews about coffee")
   - [REVIEW_META] Reviewer properties (e.g., elite reviewer, experienced reviewer)
3. Identify LOGIC: AND (all conditions must match) or OR (any condition matches)
4. DO NOT attempt to find matching items - Phase 2 will design evaluation steps.

[OUTPUT FORMAT]
===STRATEGY===
CONDITIONS:
  1. [TYPE] description - attribute.path = expected_value
  2. [TYPE] description - attribute.path = expected_value
  ...

LOGIC: AND(1, 2, ...) or OR(1, 2, ...) or complex (e.g., AND(1, OR(2, 3)))
TOTAL_ITEMS: {n_items}

===MESSAGE===
Brief notes for Phase 2 (optional)
"""

# =============================================================================
# PHASE 2: LWT Generation (Item-Aware Execution Plan)
# =============================================================================
# Phase 2 receives the strategy and generates concrete LWT steps.

PHASE2_PROMPT = """Generate LWT steps to evaluate {n_items} items against conditions.

[STRATEGY]
{strategy}

[LWT STEP FORMAT]
Each step MUST include {{(items)}} to access item data:
(step_id)=LLM('Items: {{(items)}}. Check condition X. Output matching indices: [indices]')

Example steps:
(c1)=LLM('Items: {{(items)}}. List indices where attributes.GoodForKids=True. Output: [indices]')
(c2)=LLM('Items: {{(items)}}. List indices where attributes.Ambience.hipster=True. Output: [indices]')
(c3)=LLM('Items: {{(items)}}. Check reviews for keyword work. Output: [indices]')
(final)=LLM('Results: c1={{(c1)}}, c2={{(c2)}}, c3={{(c3)}}. Intersect all. If empty, rank by partial match count. Output top-5: [indices]')

[OUTPUT - Use single quotes inside step string]
lwt_insert(1, "(c1)=LLM('Items: {{(items)}}. List indices where ...')")
lwt_insert(2, "(c2)=LLM('Items: {{(items)}}. ...')")
...
lwt_insert(N, "(final)=LLM('Results: c1={{(c1)}}, c2={{(c2)}}, ... Intersect. Output top-5: [indices]')")
done()
"""
