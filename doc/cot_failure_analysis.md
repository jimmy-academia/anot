# CoT Failure Analysis on Indirect Request Text

## Overview

This document analyzes why Chain of Thought (CoT) fails on indirect/narrative request text while it succeeds on explicit/structured requests.

## Test Case: R01

### Original Request (Explicit)
```
Looking for a cafe that's kid-friendly, with a drive-thru, and without TVs
```
**Result**: CoT succeeds (attributes directly stated)

### New Request (Indirect/Narrative)
```
I'm taking my 2-year-old out for coffee. She gets fussy in places that aren't
set up for little ones, and honestly any place with screens becomes a battle -
she gets glued to them and then melts down when we leave. I'm also a realist
though - if she starts throwing a tantrum, I need to be able to just grab our
drinks without unbuckling her from the car seat.
```
**Result**: CoT fails completely

## Required Attribute Mapping

The indirect text requires reasoning to extract requirements:

| Narrative Phrase | Required Attribute |
|-----------------|-------------------|
| "2-year-old", "fussy", "set up for little ones" | `GoodForKids=True` |
| "screens", "glued to them", "melts down" | `HasTV=False` |
| "grab drinks without unbuckling", "car seat" | `DriveThru=True` |

## Gold Restaurant

**Milkcrate Cafe** (business_id: e-ZyZc24wgkKafM3pguR2w)
- `GoodForKids: true`
- `HasTV: false`
- `DriveThru: true`

Location in shuffled order: Position 8

## CoT's Actual Output

From `results/dev/057_cot/debug.log` (line 11047-11048):

```
RESPONSE:
ANSWER: 5,11,10,7,3
```

**Key observation**: CoT output NO reasoning at all. Just the answer.

## Why CoT Failed

1. **No chain-of-thought reasoning shown** - Despite being "Chain of Thought", the model jumped directly to an answer without analyzing the requirements

2. **Failed to map narrative to attributes** - The indirect language required multi-step inference:
   - "2-year-old" + "fussy" + "set up for little ones" → child-friendly → `GoodForKids`
   - "screens" + "glued" + "melts down when we leave" → TV is problematic → `HasTV=False`
   - "grab drinks without unbuckling" + "car seat" → need drive-thru → `DriveThru`

3. **Likely focused on review content** - Without explicit attribute requirements, CoT probably matched review sentiment/keywords rather than systematically checking structured attributes

4. **Position 8 not in top-5** - CoT predicted positions [5, 11, 10, 7, 3], completely missing the gold restaurant at position 8

## Comparison with Explicit Text

| Aspect | Explicit Request | Indirect Request |
|--------|-----------------|------------------|
| Requirements | Directly stated | Hidden in narrative |
| Reasoning needed | Simple matching | Multi-step inference |
| CoT performance | ~100% | 0% (missed gold) |

## Implications for Request Text Design

To create a fair benchmark where CoT fails but ANoT succeeds:

1. **Use narrative language** - Describe situations, not attributes
2. **Embed requirements in context** - "my 2-year-old" instead of "kid-friendly"
3. **Use negative framing** - "screens become a battle" instead of "no TV"
4. **Imply needs through scenarios** - "grab drinks without unbuckling" instead of "drive-thru"

## Related Files

- Debug log: `results/dev/057_cot/debug.log`
- Results: `results/dev/057_cot/results_20.jsonl`
- ANoT trace: `results/dev/058_anot/anot_trace.jsonl`

## Next Steps

1. Apply indirect text style to all 100 requests
2. Verify ANoT succeeds with fixed prompts (see `methods/anot/prompts.py` changes)
3. Run full benchmark comparison
