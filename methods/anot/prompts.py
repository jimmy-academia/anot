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
# Phase 2 receives the strategy and generates concrete LWT steps with batching.

PHASE2_PROMPT = """Generate LWT execution steps from the strategy.

[STRATEGY FROM PHASE 1]
{strategy}

[DATA ACCESS]
- Total items: {n_items}
- Access item: {{(items)}}[idx] where idx is 1 to {n_items}
- Item fields: name, attributes, hours, reviews[], categories

[STEP PATTERNS BY CONDITION TYPE]

For [ATTR] conditions (simple attribute check):
(c1)=LLM("For items 1-{n_items}, list indices where attributes.GoodForKids=True. Output format: [indices]")

For [AMBIENCE] conditions (nested dict check):
(c2)=LLM("For items 1-{n_items}, list indices where attributes.Ambience.hipster=True. Output format: [indices]")

For [MEAL] conditions (nested dict check):
(c3)=LLM("For items 1-{n_items}, list indices where attributes.GoodForMeal.brunch=True. Output format: [indices]")

For [HOURS] conditions (time parsing):
(c4)=LLM("For items 1-{n_items}, list indices open on Friday after 21:00. Hours format: day=start-end (e.g., Friday=12:0-22:0 means 12pm-10pm). Output format: [indices]")

For [REVIEW_TEXT] conditions (MUST use batching for {n_items} > 10):
(c5.b1)=LLM("For items 1-10, check if any review text contains 'work'. Output matching indices: [indices]")
(c5.b2)=LLM("For items 11-20, check if any review text contains 'work'. Output matching indices: [indices]")
(c5.b3)=LLM("For items 21-30, check if any review text contains 'work'. Output matching indices: [indices]")
(c5.b4)=LLM("For items 31-40, check if any review text contains 'work'. Output matching indices: [indices]")
(c5.b5)=LLM("For items 41-{n_items}, check if any review text contains 'work'. Output matching indices: [indices]")
(c5.agg)=LLM("Merge these lists into one: {{(c5.b1)}}, {{(c5.b2)}}, {{(c5.b3)}}, {{(c5.b4)}}, {{(c5.b5)}}. Output combined [indices]")

[AGGREGATION STEP]
After generating steps for all conditions, add a final aggregation step:

For AND logic:
(final)=LLM("Find intersection of {{(c1)}} AND {{(c2)}} AND {{(c3.agg)}}. If empty, list items by partial match count. Output best index or top-5: [indices]")

For OR logic:
(final)=LLM("Find union of {{(c1)}} OR {{(c2)}}. Output best index or top-5: [indices]")

[TOOLS]
- lwt_list() → show current LWT steps
- lwt_insert(idx, "step") → add step at position idx
- lwt_set(idx, "step") → replace step at position idx
- done() → finish when LWT is complete

[TASK]
Generate the complete LWT for the strategy above:
1. For each condition, add appropriate evaluation step(s)
2. Use BATCHING for [REVIEW_TEXT] conditions (batches of 10 items)
3. Add final aggregation step with the correct LOGIC
4. Call done() when complete

Start by using lwt_insert() to add steps, then call done().
"""
