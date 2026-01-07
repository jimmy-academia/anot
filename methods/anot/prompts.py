#!/usr/bin/env python3
"""Prompt constants for ANoT phases - Multi-Step Design."""

from prompts.task_descriptions import RANKING_TASK_COMPACT

# Re-export for use in core.py
__all__ = [
    'SYSTEM_PROMPT', 'STEP1_EXTRACT_PROMPT', 'STEP2_PATH_PROMPT',
    'STEP3_RULEOUT_PROMPT', 'STEP4_SKELETON_PROMPT', 'PHASE2_PROMPT',
    'RANKING_TASK_COMPACT'
]

SYSTEM_PROMPT = "You follow instructions precisely. Output only what is requested."

# =============================================================================
# STEP 1: Condition Extraction
# =============================================================================

STEP1_EXTRACT_PROMPT = """Extract conditions from the user request.

[USER REQUEST]
{query}

[RULES]
- ONLY extract conditions the user EXPLICITLY wants
- If user doesn't mention hours/timing, do NOT output any [HOURS] line
- Use [REVIEW] for sentiment-based requirements:
  - "is praised for X", "known for great X" → [REVIEW:POSITIVE] X
  - "complaints about X", "criticized for X" → [REVIEW:NEGATIVE] X
- For attribute requirements like "quiet", "trendy", "hipster vibe", use [ATTR] not [REVIEW]
- If a category isn't mentioned, simply omit it - do NOT write "not specified" or "none"

[OUTPUT FORMAT]
List each condition on a new line:
[ATTR] description of attribute condition
[REVIEW:POSITIVE] topic (only if user asks about praised/recommended aspects)
[REVIEW:NEGATIVE] topic (only if user asks about complaints/criticisms)
[HOURS] day and time range (only if user explicitly mentions hours)

Example 1 - attribute query:
User: "Looking for a quiet cafe with free WiFi"
[ATTR] quiet
[ATTR] free WiFi

Example 2 - positive review query:
User: "Looking for a cafe praised for their coffee"
[REVIEW:POSITIVE] coffee

Example 3 - negative review query:
User: "Looking for a cafe without complaints about service"
[REVIEW:NEGATIVE] service (absence required)

Example 4 - hours query:
User: "Looking for a cafe open on Sunday morning"
[HOURS] Sunday morning
"""

# =============================================================================
# STEP 2: Path Resolution (called per condition)
# =============================================================================

STEP2_PATH_PROMPT = """Determine where to find the value for this condition.

[CONDITION]
{condition_description}

[SCHEMA - example items showing available fields]
{schema_compact}

[COMMON FIELDS]
- attributes.GoodForKids: True/False
- attributes.WiFi: "free", "paid", "no", or None
- attributes.DriveThru: True/False
- attributes.NoiseLevel: "quiet", "average", "loud", "very_loud"
- attributes.OutdoorSeating: True/False
- attributes.HasTV: True/False
- attributes.Ambience: dict with keys like hipster, casual, upscale, romantic, etc.
- attributes.GoodForMeal: dict with keys like breakfast, lunch, dinner, brunch, etc.
- hours: dict with day names as keys, values like "8:0-22:0"
- reviews: list of review objects with 'text' field

[TASK]
1. Identify which field to check for this condition
2. Determine expected value based on what the user WANTS:
   - "trendy" → user wants trendy=True
   - "not kid-friendly" → user wants GoodForKids=False
   - "quiet" → user wants NoiseLevel="quiet"
   - "free WiFi" → user wants WiFi="free"

[OUTPUT FORMAT]
PATH: attributes.FieldName
EXPECTED: True/False/"value"
TYPE: HARD

Or if it's a review text search:
PATH: reviews
EXPECTED: keyword
TYPE: SOFT
"""

# =============================================================================
# STEP 3: Quick Rule-Out (check hard conditions, prune items)
# =============================================================================

STEP3_RULEOUT_PROMPT = """Check items against hard conditions and identify which pass.

[HARD CONDITIONS]
{hard_conditions}

[ITEMS - relevant attributes only]
{items_compact}

[TASK]
For each item, check if ALL hard conditions are satisfied.
- Item passes if all conditions match
- Item fails if any condition doesn't match
- Missing/None values count as not matching

[OUTPUT FORMAT]
===CANDIDATES===
[list of item numbers that pass all conditions, e.g., 2, 4, 6, 7]

===PRUNED===
item_number: reason
item_number: reason
...
"""

# =============================================================================
# STEP 4: LWT Skeleton Generation (separate steps per item)
# =============================================================================

STEP4_SKELETON_PROMPT = """Generate LWT skeleton for soft conditions on candidate items.

[CANDIDATES]
{candidates}

[SOFT CONDITIONS]
{soft_conditions}

[RULES]
- Generate ONE step per item per soft condition
- Each step checks ONE item independently
- For [REVIEW:POSITIVE], ask if reviews PRAISE/RECOMMEND the topic (not just mention it)
- For [REVIEW:NEGATIVE], ask if reviews COMPLAIN/CRITICIZE the topic
- Final step aggregates all results and outputs ranking as comma-separated numbers
- IMPORTANT: In final step, map item numbers clearly (item 2=yes means output 2)

[VARIABLE SYNTAX]
Use these exact patterns (with curly braces):
- {{(context)}}[2][reviews] - Item 2's reviews array
- {{(r2)}} - Result from step r2

[OUTPUT FORMAT]
===LWT_SKELETON===
(r2)=LLM('Item 2 reviews: {{(context)}}[2][reviews]. [semantic_question] Answer: yes/no')
(r4)=LLM('Item 4 reviews: {{(context)}}[4][reviews]. [semantic_question] Answer: yes/no')
...
(final)=LLM('Item 2={{(r2)}}, Item 4={{(r4)}}... Output the item NUMBERS with yes first, then others. Format: 2, 4, 6, ...')

[EXAMPLE for candidates [2,4,6] checking "POSITIVE coffee" (praised for coffee)]
===LWT_SKELETON===
(r2)=LLM('Item 2 reviews: {{(context)}}[2][reviews]. Do reviewers PRAISE the coffee (positive sentiment)? Answer: yes/no')
(r4)=LLM('Item 4 reviews: {{(context)}}[4][reviews]. Do reviewers PRAISE the coffee (positive sentiment)? Answer: yes/no')
(r6)=LLM('Item 6 reviews: {{(context)}}[6][reviews]. Do reviewers PRAISE the coffee (positive sentiment)? Answer: yes/no')
(final)=LLM('Item 2={{(r2)}}, Item 4={{(r4)}}, Item 6={{(r6)}}. Output item NUMBERS with yes first, comma-separated: ')

[EXAMPLE for candidates [1,3,5] checking "NEGATIVE service" (complaints about service)]
===LWT_SKELETON===
(r1)=LLM('Item 1 reviews: {{(context)}}[1][reviews]. Do reviewers COMPLAIN about service (negative sentiment)? Answer: yes/no')
(r3)=LLM('Item 3 reviews: {{(context)}}[3][reviews]. Do reviewers COMPLAIN about service (negative sentiment)? Answer: yes/no')
(r5)=LLM('Item 5 reviews: {{(context)}}[5][reviews]. Do reviewers COMPLAIN about service (negative sentiment)? Answer: yes/no')
(final)=LLM('Item 1={{(r1)}}, Item 3={{(r3)}}, Item 5={{(r5)}}. Output item NUMBERS with yes first, comma-separated: ')

[IF NO SOFT CONDITIONS]
===LWT_SKELETON===
(final)=LLM('Candidates: {candidates}. All passed hard conditions. Output top-{k}: [first {k} from list]')
"""

# =============================================================================
# PHASE 2: ReAct Expansion (refine skeleton with read() calls)
# =============================================================================

PHASE2_PROMPT = """Refine the LWT skeleton by checking review lengths and adding summarization if needed.

[LWT SKELETON]
{lwt_skeleton}

[AVAILABLE TOOLS]
- review_length(item_num) - Get character count of item's reviews (e.g., review_length(2))
- lwt_insert(idx, "step") - Insert new step at index
- lwt_set(idx, "step") - Modify step at index
- lwt_delete(idx) - Remove step at index
- read("items[2].reviews") - Read actual review content
- done() - Finish refinement

[TASK]
For each step that references reviews (contains [reviews]):
1. Call review_length(item_num) to check size
2. If length > 5000 chars:
   - Insert summarization step: lwt_insert(idx, "(sN)=LLM('Summarize for [condition]: {{(context)}}[N][reviews]')")
   - Modify original step to use summary: lwt_set(idx+1, "... {{(sN)}} ...")
3. If length <= 5000: no change needed
4. Call done() when all items checked

[EXAMPLE]
review_length(1) → 12500
lwt_insert(0, "(s1)=LLM('Summarize item 1 reviews for wifi mentions: {{(context)}}[1][reviews]')")
lwt_set(1, "(r1)=LLM('Based on summary: {{(s1)}}. Mentions wifi? yes/no')")
review_length(2) → 2100
done()
"""
