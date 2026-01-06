# Benchmark Statistics

Comprehensive statistics for the philly_cafes benchmark dataset.

## Overview

| Metric | Value |
|--------|-------|
| Total Restaurants | 50 |
| Total Requests | 100 |
| Request Groups | 10 |
| Validation Rate | 100% |

## Request Groups Distribution

| Group | Count | Structure Type |
|-------|-------|----------------|
| G01 | 10 | Simple AND |
| G02 | 10 | Simple OR |
| G03 | 10 | AND-OR Combination |
| G04 | 10 | Review Metadata Weighting |
| G05 | 10 | Triple OR with Anchor |
| G06 | 10 | Nested OR+AND |
| G07 | 10 | Chained OR |
| G08 | 10 | Unbalanced Structure |
| G09 | 10 | Direct Friends (1-hop) |
| G10 | 10 | Social Circle (2-hop) |

## Evidence Type Distribution

| Evidence Type | Count | Percentage |
|---------------|-------|------------|
| item_meta | 196 | 47.3% |
| review_text | 136 | 32.9% |
| review_meta | 49 | 11.8% |
| social_filter | 20 | 4.8% |
| item_meta_hours | 13 | 3.1% |

**Total conditions across all requests**: 414

## Top 20 Most Used Conditions

| Condition | Count |
|-----------|-------|
| work_reviews | 10 |
| full_bar | 8 |
| quiet | 8 |
| breakfast_reviews | 8 |
| coffee_reviews | 8 |
| has_tv | 7 |
| byob | 7 |
| favorite_reviews | 7 |
| no_tv | 6 |
| takeout | 6 |
| review_meta_elite_status_work | 6 |
| music_reviews | 6 |
| bike_parking | 5 |
| wifi_free | 5 |
| price_cheap | 5 |
| casual_vibe | 5 |
| latte_reviews | 5 |
| brunch_reviews | 5 |
| fast_reviews | 5 |
| friendly_reviews | 5 |

## Restaurant Coverage

**Note**: All 80 requests now use the top 20 restaurants by gold frequency, achieving 100% coverage at N=20 scaling.

### Usage Frequency

| Usage Count | Restaurants |
|-------------|-------------|
| 5 times | [2], [3], [9], [13], [18] |
| 4 times | [1], [5], [7], [10], [11], [12], [14], [16], [17], [19] |
| 3 times | [0], [4], [21], [25], [32] |
| 0 times | [6], [8], [15], [20], [22-31], [33-49] |

### Complete Restaurant Usage Table

| Index | Restaurant Name | Usage Count | Requests |
|-------|-----------------|-------------|----------|
| 0 | Milkcrate Cafe | 3 | R01, R31, R41 |
| 1 | Tria Cafe Rittenhouse | 4 | R02, R13, R22, R42 |
| 2 | Front Street Cafe | 5 | R03, R18, R19, R40, R46 |
| 3 | MilkBoy | 5 | R11, R24, R26, R32, R47 |
| 4 | Kung Fu Tea | 3 | R04, R35, R48 |
| 5 | Function Coffee Labs | 4 | R07, R49, R59, R69 |
| 6 | The Bubble House | 0 | - |
| 7 | Swiss Haus Cafe & Pastry Bar | 4 | R05, R37, R50, R71 |
| 8 | Le Pain Quotidien | 0 | - |
| 9 | Gran Caffe L'Aquila | 5 | R12, R28, R29, R33, R72 |
| 10 | Thirsty Dice | 4 | R17, R30, R38, R73 |
| 11 | Cafe La Maude | 4 | R39, R58, R68, R74 |
| 12 | Hinge Cafe | 4 | R34, R57, R67, R75 |
| 13 | Steap and Grind | 5 | R06, R15, R23, R27, R76 |
| 14 | La Colombe Coffee | 4 | R08, R56, R66, R77 |
| 15 | Last Drop | 0 | - |
| 16 | Elixr Coffee Roasters | 4 | R10, R21, R36, R78 |
| 17 | United By Blue | 4 | R16, R25, R60, R70 |
| 18 | Chapterhouse Café & Gallery | 5 | R09, R20, R54, R64, R79 |
| 19 | Sabrina's Café | 4 | R14, R55, R65, R80 |
| 20 | The Bakeshop on 20th | 0 | - |
| 21 | K'Far Cafe | 3 | R43, R53, R63 |
| 22 | The Green Line Cafe | 0 | - |
| 23 | La Colombe Coffee | 0 | - |
| 24 | Manakeesh Cafe Bakery & Grill | 0 | - |
| 25 | Frieda | 3 | R44, R52, R62 |
| 26 | Plenty Café | 0 | - |
| 27 | Bluestone Lane | 0 | - |
| 28 | One Shot Coffee | 0 | - |
| 29 | Saxbys Rittenhouse | 0 | - |
| 30 | Black & Brew | 0 | - |
| 31 | Metropolitan Bakery | 0 | - |
| 32 | Saxbys | 3 | R45, R51, R61 |
| 33-49 | (Various) | 0 | - |

## Structural Complexity Analysis

### Nesting Depth by Group

| Group | Max Depth | Avg Conditions | Structure Pattern |
|-------|-----------|----------------|-------------------|
| G01 | 1 | 3-4 | AND(c1, c2, c3) |
| G02 | 2 | 3-4 | AND/OR combinations |
| G03 | 2 | 3-5 | AND(anchor, OR(...)) |
| G04 | 2 | 3-5 | AND(conditions, weighted_meta) |
| G05 | 2 | 4-6 | AND(anchors, OR(a,b,c)) |
| G06 | 3 | 4-6 | AND(anchor, OR(AND,AND)) |
| G07 | 2 | 5-7 | AND(anchor, OR, OR) |
| G08 | 3 | 4-6 | AND(anchor, OR(simple, AND)) |
| G09 | 1 | 1 | 1HOP(friends, pattern) |
| G10 | 1 | 1 | 2HOP(friends, pattern) |

### Evaluation Difficulty Progression

```
G01 → G02 → G03 → G04 → G05 → G06 → G07 → G08 → G09 → G10
 │      │      │      │      │      │      │      │      │      │
 ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼      ▼
Easy   Easy  Medium Medium Medium  High  High  High Medium  High
```

Note: G09-G10 test social/relational reasoning rather than logical complexity.

## Condition Category Distribution

| Category | Conditions Used | Total Count |
|----------|-----------------|-------------|
| price | 3 | 8 |
| noise | 2 | 5 |
| wifi | 3 | 9 |
| hours | 3 | 3 |
| meal | 3 | 7 |
| ambience | 3 | 7 |
| review_patterns | 32 | 125 |
| review_meta | 17 | 39 |
| social_filter | 20 | 20 |
