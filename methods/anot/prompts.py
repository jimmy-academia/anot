#!/usr/bin/env python3
"""Prompt constants for ANoT phases."""

from prompts.task_descriptions import RANKING_TASK_COMPACT

# Re-export for use in core.py
__all__ = ['SYSTEM_PROMPT', 'PHASE1_PROMPT', 'PHASE2_PROMPT', 'RANKING_TASK_COMPACT']

SYSTEM_PROMPT = "You follow instructions precisely. Output only what is requested."

PHASE1_PROMPT = """Analyze the user request and rank items.

{task_description}

[ITEMS - 1-indexed]
{items_compact}

[ITEM FORMAT]
- Attrs: Full attribute values. Nested dicts shown as {{key:value,key:value}}
  - Ambience={{hipster:True,casual:True,...}} - look for True values
  - GoodForMeal={{breakfast:True,lunch:False,...}} - look for True values
- Hours: day=start-end (e.g., Friday=12:0-22:0 means open 12pm-10pm)
- Reviews: text with keywords to search

[TASK]
1. READ the user request carefully. Extract ONLY conditions mentioned in the request.
   - If request says "upscale" → look for Ambience.upscale=True
   - If request says "free WiFi" → look for WiFi=free
   - If request says "coat check" → look for CoatCheck=True
   - If request says "full bar" → look for Alcohol=full_bar
   - If request says "hipster vibe" → look for Ambience.hipster=True
   DO NOT add conditions not in the request!
2. Find items where the requested conditions are satisfied (use 1-indexed numbers)
3. If multiple items match, include ALL of them in REMAINING

[OUTPUT FORMAT]
===LWT_SKELETON===
(final)=LLM("Find the best item for: {{(query)}}. Candidates: [REMAINING INDICES]. Output the best index number only.")

===MESSAGE===
CONDITIONS: <list conditions from user request - ONLY what user asked for>
REMAINING: <1-indexed item numbers that match>
NEEDS_EXPANSION: no
"""

PHASE2_PROMPT = """Check if the LWT skeleton needs expansion, then call done().

[MESSAGE FROM PHASE 1]
{message}

[CURRENT LWT]
{lwt_skeleton}

[TOOLS]
- done() → finish (call this when skeleton is complete)
- lwt_set(idx, "step") → replace step at index
- lwt_insert(idx, "step") → add step (only if needed)
- read(path) → get data (only if needed)

[IMPORTANT: SUBSTITUTE REMAINING INDICES]
If the LWT contains "[REMAINING INDICES]", you MUST replace it with actual indices from REMAINING in the message.

Example:
  MESSAGE: REMAINING: 4, 7, 13
  LWT: 0: (final)=LLM("...Candidates: [REMAINING INDICES]...")
  Action: lwt_set(0, "(final)=LLM(\\"...Candidates: [4, 7, 13]...\\")")
  Then: done()

[DECISION]
1. First, if LWT contains "[REMAINING INDICES]", use lwt_set to substitute with actual indices from REMAINING
2. Then look at NEEDS_EXPANSION:
   - If "no" → call done()
   - If "yes" → use tools to add steps, then done()

What is your action?
"""
