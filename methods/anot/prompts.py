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
# CRITICAL: Each step must be SELF-CONTAINED with the actual condition embedded.

PHASE2_PROMPT = """Generate LWT steps to evaluate {n_items} items against conditions.

[STRATEGY FROM PHASE 1]
{strategy}

[AVAILABLE TOOLS]
- read("items[0].attributes") - Probe data structure, see available fields
- read("items[0].attributes.GoodForKids") - Get specific value from item 0
- lwt_insert(idx, step) - Add LWT step
- done() - Finish

[PATH SYNTAX for LWT steps]
Use {{(context)}}[path] to access restaurant data in Phase 3:
- {{(context)}}[1] - Item 1 (1-indexed)
- {{(context)}}[1][attributes] - Item 1's attributes dict
- {{(context)}}[1][attributes][GoodForKids] - Single value (True/False)
- {{(context)}}[1][attributes][Ambience][hipster] - Nested value
- {{(context)}}[1][hours] - Item 1's hours dict

[STEP TEMPLATES]
CRITICAL: You MUST list ALL items explicitly. Do NOT use "..." - it won't be expanded!

For [ATTR] conditions - list EVERY item's value:
  (c1)=LLM('1={{(context)}}[1][attributes][GoodForKids], 2={{(context)}}[2][attributes][GoodForKids], 3={{(context)}}[3][attributes][GoodForKids], 4={{(context)}}[4][attributes][GoodForKids], 5={{(context)}}[5][attributes][GoodForKids]. Which are True? Output: [indices]')

For nested attributes (Ambience, GoodForMeal) - list ALL:
  (c2)=LLM('1={{(context)}}[1][attributes][Ambience][hipster], 2={{(context)}}[2][attributes][Ambience][hipster], 3={{(context)}}[3][attributes][Ambience][hipster], 4={{(context)}}[4][attributes][Ambience][hipster], 5={{(context)}}[5][attributes][Ambience][hipster]. Which are True? Output: [indices]')

Final aggregation:
  (final)=LLM('c1={{(c1)}}, c2={{(c2)}}. Score items: +1 per condition matched. Rank by score DESC. Output top-5: [best,2nd,3rd,4th,5th]')

[PROCESS]
1. Optionally use read() to verify field paths exist
2. Generate LWT steps for each condition
3. Generate final aggregation step
4. Call done()

[EXAMPLE for 10 items]
read("items[0].attributes")  # See available fields
lwt_insert(1, "(c1)=LLM('GoodForKids: 1={{(context)}}[1][attributes][GoodForKids], 2={{(context)}}[2][attributes][GoodForKids], 3={{(context)}}[3][attributes][GoodForKids], 4={{(context)}}[4][attributes][GoodForKids], 5={{(context)}}[5][attributes][GoodForKids], 6={{(context)}}[6][attributes][GoodForKids], 7={{(context)}}[7][attributes][GoodForKids], 8={{(context)}}[8][attributes][GoodForKids], 9={{(context)}}[9][attributes][GoodForKids], 10={{(context)}}[10][attributes][GoodForKids]. Which are True? Output: [indices]')")
lwt_insert(2, "(c2)=LLM('WiFi: 1={{(context)}}[1][attributes][WiFi], 2={{(context)}}[2][attributes][WiFi], 3={{(context)}}[3][attributes][WiFi], 4={{(context)}}[4][attributes][WiFi], 5={{(context)}}[5][attributes][WiFi], 6={{(context)}}[6][attributes][WiFi], 7={{(context)}}[7][attributes][WiFi], 8={{(context)}}[8][attributes][WiFi], 9={{(context)}}[9][attributes][WiFi], 10={{(context)}}[10][attributes][WiFi]. Which are free? Output: [indices]')")
lwt_insert(3, "(final)=LLM('c1={{(c1)}}, c2={{(c2)}}. Score: +1 per match. Output top-5: [best,2nd,3rd,4th,5th]')")
done()
"""
