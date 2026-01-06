# Philadelphia Cafes Benchmark Dataset

A structured benchmark dataset for evaluating LLM reasoning on restaurant recommendation tasks with formal logical structures.

## Overview

- **50 restaurants** with attributes and reviews
- **100 requests** across 10 structural complexity groups (G01-G10)
- **100% validation** - each request matches exactly one restaurant

## Dataset Files

| File | Description |
|------|-------------|
| `restaurants.jsonl` | 50 Philadelphia cafe profiles with attributes |
| `reviews.jsonl` | Customer reviews for each restaurant |
| `requests.jsonl` | 100 benchmark requests with logical structures |
| `groundtruth.jsonl` | Gold answers and validation status |
| `user_mapping.json` | Synthetic user data for social filter (G09-G10) |
| `condition_matrix.json` | Full condition satisfaction matrix |
| `condition_summary.md` | Human-readable condition analysis |

## Request Groups

### G01: Simple AND (R01-R10)
**Structure**: `AND(condition1, condition2, condition3)`

Basic conjunction of 2-4 conditions. Tests fundamental attribute matching.

**Example R01**:
```
"Looking for a quiet cafe with free WiFi that's good for studying"
AND(noise_quiet, wifi_free, study_reviews)
Gold: [0] Milkcrate Cafe
```

**Complexity**: Low - straightforward attribute checking

---

### G02: Simple OR (R11-R20)
**Structure**: `OR(condition1, condition2)` or `AND(anchor, OR(...))`

Tests disjunctive reasoning - any one condition suffices.

**Example R13**:
```
"Looking for a cafe that's either good for brunch or has outdoor seating"
OR(meal_brunch, outdoor_yes)
Gold: [1] Tria Cafe Rittenhouse
```

**Complexity**: Low-Medium - requires checking multiple paths

---

### G03: AND-OR Combination (R21-R30)
**Structure**: `AND(condition1, OR(condition2, condition3))`

Nested structure with anchor + disjunction.

**Example R22**:
```
"Looking for a mid-priced cafe with either 'cozy' or 'comfortable' mentioned in reviews"
AND(price_mid, OR(cozy, comfortable_reviews))
Gold: [1] Tria Cafe Rittenhouse
```

**Complexity**: Medium - requires understanding nested logic

---

### G04: Review Metadata Weighting (R31-R40)
**Structure**: `AND(conditions, credibility_count_condition)`

Uses credibility-count evaluation: "At least N credible reviewers (above percentile) mention pattern"

**Evaluation Logic**:
- Credibility threshold: 50th percentile of non-zero metadata values
- Minimum credible matches: 2 reviewers must agree
- Weight fields: `review_count`, `fans`, `elite` years, `useful` votes

**Example R33**:
```
"Looking for a cafe with a full bar, where elite reviewers mention 'love', without coat check, offers delivery, and good for dinner"
AND(full_bar, no_coat_check, elite_love, delivery, dinner)
Gold: [9] Gran Caffe L'Aquila
```

**Complexity**: Medium-High - requires credibility-aware evaluation

---

### G05: Triple OR with Anchor (R41-R50)
**Structure**: `AND(anchor1, anchor2, OR(opt1, opt2, opt3))`

Multiple anchoring conditions with three-way disjunction.

**Example R41**:
```
"Looking for a cafe with a drive-thru that has either 'coffee', 'breakfast', or 'friendly' mentioned"
AND(drive_thru, OR(coffee_reviews, breakfast_reviews, friendly_reviews))
Gold: [0] Milkcrate Cafe
```

**Complexity**: Medium - unique anchor simplifies, OR adds options

---

### G06: Nested OR+AND (R51-R60)
**Structure**: `AND(anchor, OR(AND(a,b), AND(c,d)))`

Disjunction of conjunctions - either (A AND B) or (C AND D).

**Example R55**:
```
"Looking for a cafe with free corkage that's either (organic AND music) or (work AND wifi)"
AND(byob_corkage_free, OR(AND(organic, music), AND(work, wifi)))
Gold: [42] Mugshots Coffeehouse
```

**Complexity**: High - requires evaluating nested AND blocks within OR

---

### G07: Chained OR (R61-R70)
**Structure**: `AND(anchor, OR(a,b), OR(c,d))`

Multiple independent OR blocks that all must have at least one match.

**Example R66**:
```
"Looking for a hipster cafe good for lunch, open Monday afternoon,
 that either has 'sandwich' or 'work' mentioned,
 and either 'meeting' or popular reviewers mention 'work'"
AND(hipster, lunch, hours_monday_afternoon, OR(sandwich,work), OR(meeting,popular_work))
Gold: [47] Rocket Cat Cafe
```

**Complexity**: High - multiple disjunctions must all be satisfied

---

### G08: Unbalanced Structure (R71-R80)
**Structure**: `AND(anchor, simple, OR(opt, AND(nested1, nested2)))`

Asymmetric structure with one simple OR option and one complex AND option.

**Example R71**:
```
"Looking for a quiet cafe with beer and wine that's either
 where reviews mention 'slow', or both elite reviewers mention 'work' and 'best'"
AND(alcohol_beer_wine, noise_quiet, OR(slow_reviews, AND(elite_work, best)))
Gold: [7] Swiss Haus Cafe & Pastry Bar
```

**Complexity**: High - unbalanced complexity in OR branches

---

### G09: Direct Friends / 1-Hop (R81-R90)
**Structure**: `1HOP([friend_list], pattern)`

Filter reviews to those from users directly in the provided friend list. Tests social/relational reasoning with direct connections.

**Evaluation Logic**:
- Reviewer's name must be in the query's friend list
- Reviewer must mention the required pattern

**Example R81**:
```
"My friend Alice recommended some cafes. Looking for one where she mentions it's 'cozy'"
1HOP(['Alice'], 'cozy')
Gold: [0] Milkcrate Cafe
```

**Complexity**: Medium - requires matching reviewer identity + pattern

---

### G10: Social Circle / 2-Hop (R91-R100)
**Structure**: `2HOP([friend_list], pattern)`

Filter reviews to those from users who are either direct friends OR friends-of-friends. Tests broader social graph reasoning.

**Evaluation Logic**:
- Reviewer's name is in the friend list (direct friend), OR
- Reviewer has a friend whose name is in the friend list (friend-of-friend)
- Reviewer must mention the required pattern

**Example R91**:
```
"Looking for a cafe recommended by my social circle. My friend Bob or his friends mention 'recommend'"
2HOP(['Bob'], 'recommend')
Gold: [10] Thirsty Dice
```

**Complexity**: High - requires traversing social graph + pattern matching

---

## Shorthand Notation

Each request includes a `shorthand` field with compact structure notation:

| Group | Pattern | Example |
|-------|---------|---------|
| G01 | `AND(a, b, c)` | `AND(drive_thru, good_for_kids, no_tv)` |
| G02 | `AND(anchor, OR(a, b))` | `AND(full_bar, OR(music, live_music))` |
| G03 | `AND(a, OR(b, c))` | `AND(price_mid, OR(cozy, comfortable))` |
| G04 | `AND(a, b, review_meta_*)` | `AND(full_bar, review_meta_elite_status_love)` |
| G05 | `AND(a, OR(b, c, d, e))` | `AND(drive_thru, OR(love, breakfast, popular_best, elite_love))` |
| G06 | `AND(a, OR(AND(b,c), AND(d,e)))` | `AND(takeout_no, OR(AND(romantic, coffee), AND(espresso, latte)))` |
| G07 | `AND(a, OR(b,c), OR(d,e))` | `AND(budget, byob, OR(cozy, romantic), OR(coffee, espresso))` |
| G08 | `AND(a, OR(b, AND(c,d)))` | `AND(quiet, OR(slow, AND(elite_work, best)))` |
| G09 | `1HOP([friends], pattern)` | `1HOP(['Alice'], 'cozy')` |
| G10 | `2HOP([friends], pattern)` | `2HOP(['Bob'], 'recommend')` |

---

## Evidence Types Used

| Type | Count | Description |
|------|-------|-------------|
| `item_meta` | ~200 | Restaurant attributes (price, noise, WiFi, etc.) |
| `item_meta_hours` | ~30 | Operating hour conditions |
| `review_text` | ~100 | Pattern matching in reviews |
| `review_meta` | ~20 | Credibility-count patterns (G04) |
| `social_filter` | 20 | Social graph filtering (G09-G10) |

## Restaurant Coverage

All 50 restaurants are used as gold answers, with distribution across groups ensuring each restaurant appears 1-3 times.

| Restaurant Index | Usage Count | Example Requests |
|------------------|-------------|------------------|
| [0] Milkcrate Cafe | 3 | R01, R31, R41 |
| [1] Tria Cafe | 3 | R02, R13, R42 |
| [2] Front Street Cafe | 2 | R03, R18 |
| ... | ... | ... |

## Validation

```bash
# Validate all requests
.venv/bin/python -m data.validate philly_cafes

# Expected output:
# Validation: 100/100 = 100%
# All 100 requests validated successfully!
```

## Usage in Evaluation

```python
from data.validate import load_jsonl

# Load data
restaurants = load_jsonl('data/philly_cafes/restaurants.jsonl')
requests = load_jsonl('data/philly_cafes/requests.jsonl')
groundtruth = load_jsonl('data/philly_cafes/groundtruth.jsonl')

# Each request has:
# - id: "R01" to "R100"
# - group: "G01" to "G10"
# - scenario: Persona-based name (e.g., "Busy Parent", "Friend Recommendation")
# - text: Natural language request
# - shorthand: Compact notation (e.g., "AND(a, OR(b, c))" or "1HOP(['Alice'], 'cozy')")
# - structure: Formal logical structure (JSON)
# - gold_restaurant: Business ID of correct answer

# Groundtruth has:
# - request_id: Matches request.id
# - gold_restaurant: Business ID
# - gold_idx: Index in restaurants list (0-49)
# - status: "ok" for all 100 requests
```

## Design Methodology

See `doc/condition_design.md` for the complete bottom-up anchor-first design methodology used to create this benchmark.

Key principles:
1. Build condition satisfaction matrix first
2. Identify unique identifiers for each restaurant
3. Design requests around anchors to ensure uniqueness
4. Add OR complexity for evaluation challenge
5. Validate 100% unique matches
