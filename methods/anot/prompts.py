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
- Distinguish between review types:
  - "is praised for X", "known for great X" → [REVIEW:POSITIVE] X (sentiment check)
  - "complaints about X", "criticized for X" → [REVIEW:NEGATIVE] X (sentiment check)
  - "has reviews mentioning X", "reviews mention X" → [REVIEW:MENTION] X (keyword check)
- For attribute requirements like "quiet", "trendy", "hipster vibe", use [ATTR] not [REVIEW]
- For social/friend filters like "my friend X reviewed", use [SOCIAL] friend_name, keyword
- If a category isn't mentioned, simply omit it - do NOT write "not specified" or "none"

[OUTPUT FORMAT]
List each condition on a new line:
[ATTR] description of attribute condition
[REVIEW:POSITIVE] topic (only for praised/recommended aspects)
[REVIEW:NEGATIVE] topic (only for complaints/criticisms)
[REVIEW:MENTION] keyword (only for "reviews mention X" / "has reviews mentioning X")
[HOURS] day and time range (only if user explicitly mentions hours)
[SOCIAL] friend_name, keyword (only if user mentions friend's review)

Example 1 - attribute query:
User: "Looking for a quiet cafe with free WiFi"
[ATTR] quiet
[ATTR] free WiFi

Example 2 - positive sentiment review query:
User: "Looking for a cafe praised for their coffee"
[REVIEW:POSITIVE] coffee

Example 3 - keyword mention query:
User: "Looking for a cafe with reviews mentioning 'cozy'"
[REVIEW:MENTION] cozy

Example 4 - hours query:
User: "Looking for a cafe open on Sunday morning"
[HOURS] Sunday morning

Example 5 - social filter query:
User: "Looking for a cafe that my friend Kevin reviewed mentioning 'place'"
[SOCIAL] Kevin, place
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
- For [REVIEW:POSITIVE], ask if reviews PRAISE/RECOMMEND the topic (sentiment check)
- For [REVIEW:NEGATIVE], ask if reviews COMPLAIN/CRITICIZE the topic (sentiment check)
- For [REVIEW:MENTION], ask if reviews MENTION the keyword (presence check, no sentiment)
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

[EXAMPLE for candidates [2,4,6] checking "MENTION cozy" (reviews mention cozy)]
===LWT_SKELETON===
(r2)=LLM('Item 2 reviews: {{(context)}}[2][reviews]. Do reviews MENTION the word cozy? Answer: yes/no')
(r4)=LLM('Item 4 reviews: {{(context)}}[4][reviews]. Do reviews MENTION the word cozy? Answer: yes/no')
(r6)=LLM('Item 6 reviews: {{(context)}}[6][reviews]. Do reviews MENTION the word cozy? Answer: yes/no')
(final)=LLM('Item 2={{(r2)}}, Item 4={{(r4)}}, Item 6={{(r6)}}. Output item NUMBERS with yes first, comma-separated: ')

[IF NO SOFT CONDITIONS]
===LWT_SKELETON===
(final)=LLM('Candidates: {candidates}. All passed hard conditions. Output top-{k}: [first {k} from list]')
"""

# =============================================================================
# PHASE 2: ReAct Expansion (refine skeleton with slice syntax for long reviews)
# =============================================================================

PHASE2_PROMPT = """Refine the LWT skeleton by handling long reviews using slice syntax.

[LWT SKELETON]
{lwt_skeleton}

[TASK]
Analyze the LWT skeleton above. For each step that references reviews:
1. Identify the item number and what keyword/topic is being searched
2. Check if reviews are long and need slicing
3. Modify steps to use slice syntax for long reviews

[AVAILABLE TOOLS]
- get_review_lengths(item_num) - Get per-review char counts, returns JSON array [1200, 5400, 800]
- keyword_search(item_num, "keyword") - Find keyword positions in reviews, returns JSON with matches
- get_review_snippet(item_num, review_idx, start, length) - Preview text snippet
- lwt_set(idx, "step") - Replace step at index with new step
- lwt_insert(idx, "step") - Insert new step at index
- lwt_delete(idx) - Remove step at index
- done() - Finish refinement

[SLICE SYNTAX]
Use Python-style slices in variable references to truncate:
- {{{{(context)}}}}[N][reviews][R][text][start:end] - Slice review R's text from start to end
- {{{{(context)}}}}[N][reviews][0:K] - Only first K reviews
- {{{{(context)}}}}[N][reviews][R][text][:3000] - First 3000 chars of review R

[STRATEGY]
For each item step that references reviews:
1. get_review_lengths(item_num) to find long reviews (> 3000 chars)
2. If any review > 3000 chars:
   a. Infer the keyword from the LWT step (e.g., "coffee" from "Praises coffee?")
   b. keyword_search(item_num, "keyword") to find where keyword appears
   c. If keyword found at position P in review R:
      - Calculate slice: start = max(0, P - 1500), end = P + 1500
      - lwt_set to use slice syntax: {{{{(context)}}}}[N][reviews][R][text][start:end]
   d. If no keyword match in a long review: can skip that review or use [:3000]
3. If all reviews are short (< 3000): no change needed
4. done() when all items processed

[EXAMPLE]
Initial LWT step 0:
(r2)=LLM('Reviews: {{{{(context)}}}}[2][reviews]. Praises coffee? yes/no')

get_review_lengths(2) → [1200, 5400, 800]
# Review 1 is 5400 chars (> 3000), reviews 0 and 2 are short

keyword_search(2, "coffee") → {{"matches": [{{"review": 1, "positions": [2100], "length": 5400}}], "no_match_reviews": [0, 2], "total_matches": 1}}
# Found "coffee" at position 2100 in review 1

lwt_set(0, "(r2)=LLM('Reviews: {{{{(context)}}}}[2][reviews][0], {{{{(context)}}}}[2][reviews][1][text][600:3600], {{{{(context)}}}}[2][reviews][2]. Praises coffee? yes/no')")
# Keep reviews 0 and 2 full (short), slice review 1 around the keyword match (600 to 3600)

done()
"""
