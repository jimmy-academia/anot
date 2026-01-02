# Ground Truth Selection: philly_cafes

Documentation of the process for creating the ground truth dataset for evaluating LLM prompting methods.

---

## Overview

**Goal**: Create a curated evaluation dataset with:
- 20 restaurants (from 112 in source)
- 20 reviews per restaurant (400 total, from 4302 in source)
- 50 requests in 5 groups of 10, each with exactly 1 correct answer

**Source Data**: `preprocessing/output/philly_cafes/`
**Output**: `data/philly_cafes/`

---

## Data Sources

```
preprocessing/output/philly_cafes/
├── restaurants.jsonl   # 112 restaurants with LLM scores
├── reviews.jsonl       # 4302 reviews with user metadata
├── analysis.json       # Attribute distributions
└── meta.json           # Selection parameters (city: Philadelphia, categories: Coffee & Tea, Cafes)
```

---

## Restaurant Selection

### Selection Criteria

1. **Minimum 20 reviews** - Ensures enough content for review selection
2. **Rare/unique features** - Enables single-answer requests
3. **Diverse attribute combinations** - Covers all feature types needed for requests
4. **Good feature coverage** - Each feature should be represented

### Feature Analysis

Before selection, we analyzed the source data to identify rare and unique features:

```
RARE FEATURES IN SOURCE DATA:

DriveThru=True:       1 restaurant  (Milkcrate Cafe)
CoatCheck=True:       2 restaurants (Front Street Cafe, Tria Cafe Rittenhouse)
PriceRange=3:         1 restaurant  (Tria Cafe Rittenhouse)
NoiseLevel=loud:      2 restaurants (MilkBoy, Kung Fu Tea)
NoiseLevel=quiet:    17 restaurants
Alcohol=full_bar:     8 restaurants
Alcohol=beer_and_wine: 6 restaurants
HappyHour=True:      10 restaurants
DogsAllowed=True:    15 restaurants
BYOB=True:            9 restaurants
WiFi=no:              2 restaurants (MilkBoy, La Colombe Coffee)
Ambience.hipster:     3 restaurants
Ambience.trendy:      4 restaurants
```

### Selected 20 Restaurants

| # | Name | Business ID | Key Features |
|---|------|-------------|--------------|
| 1 | Milkcrate Cafe | e-ZyZc24wgkKafM3pguR2w | DriveThru (unique!), Hipster, Outdoor |
| 2 | Tria Cafe Rittenhouse | eJaeTZlIdM3HWCq__Ve4Wg | Price$3 (unique!), CoatCheck, BeerWine, Dogs, Trendy |
| 3 | Front Street Cafe | JrG4NINLspXPNhSXg7Q07Q | CoatCheck, FullBar, HappyHour, Hipster |
| 4 | MilkBoy | V_jy9Aemc3kjznqhbsu_Dg | Loud, FullBar, HappyHour, NoWiFi |
| 5 | Kung Fu Tea | 3yW8-dUi1wwCEf0URxUA7A | Loud, NoOutdoor, Kids |
| 6 | Function Coffee Labs | BaSwNEingTmrBw4shffK5w | BYOB, Dogs, Hipster, Trendy |
| 7 | The Bubble House | 8Wq0LZSuHdPTlleQD5sU_w | FullBar, Outdoor, Kids |
| 8 | Swiss Haus Cafe & Pastry Bar | vCHNWdW-ys-nWUx3Cpvk8Q | Quiet, BeerWine, NoOutdoor |
| 9 | Le Pain Quotidien | kj3Lyh9KooU8GcRBbMDQWQ | HappyHour, Outdoor, Kids |
| 10 | Gran Caffe L'Aquila | -cEFKAznWmI0cledNOIQ7w | FullBar, HappyHour, Outdoor |
| 11 | Thirsty Dice | 1klRUBB6LfKCotq75BVmbA | FullBar, HappyHour, Kids (board game cafe) |
| 12 | Cafe La Maude | K7KHmHzxNwzqiijSJeKe_A | BYOB, Dogs, Outdoor |
| 13 | Hinge Cafe | zjTBfbvbN2Ps6_Ar0w-fuQ | BYOB, Outdoor |
| 14 | Steap and Grind | 3UBG2rwjgP-6ifTAuKl3Gg | Quiet, Dogs, Outdoor (tea focus) |
| 15 | La Colombe Coffee | htO_nlxkEsYHzDrtbiUxew | NoOutdoor, NoWiFi |
| 16 | Last Drop | lh3ApskP-4XVdsQ-82792g | Quiet, Outdoor, Kids |
| 17 | Elixr Coffee Roasters | oqbhVgliVJH-iRa3AnD-3A | Quiet, Trendy |
| 18 | United By Blue | ZpgVL2z1kgRi954c9m9INw | Dogs, Outdoor, Trendy |
| 19 | Chapterhouse Cafe & Gallery | 7hpUoYdAVToZXwuPRgoqdA | Dogs, NoOutdoor (bookstore cafe) |
| 20 | Sabrina's Cafe | iUZEGx29miZObLd6_lt7Vg | Dogs, Outdoor, Kids (famous brunch) |

### Feature Matrix

```
Name                                DrT CoC BYO $$$ Noise     Alcohol   HH  Dog Out Kid WiFi  Hip Trd
--------------------------------------------------------------------------------------------------------------
Milkcrate Cafe                      Y   .   .   1   average   none      .   .   Y   Y   free  Y   .
Tria Cafe Rittenhouse               .   Y   .   3   average   beer_wine .   Y   Y   .   free  .   Y
Front Street Cafe                   .   Y   .   2   average   full_bar  Y   .   Y   Y   free  Y   .
MilkBoy                             .   .   .   2   loud      full_bar  Y   .   Y   .   no    .   .
Kung Fu Tea                         .   .   .   1   loud      none      .   .   N   Y   free  .   .
Function Coffee Labs                .   .   Y   1   average   none      .   Y   Y   Y   free  Y   Y
The Bubble House                    .   .   .   2   ?         full_bar  .   .   Y   Y   free  .   .
Swiss Haus Cafe & Pastry Bar        .   .   .   2   quiet     beer_wine .   .   N   Y   free  .   .
Le Pain Quotidien                   .   .   .   2   average   none      Y   .   Y   Y   free  .   .
Gran Caffe L'Aquila                 .   .   .   2   average   full_bar  Y   .   Y   Y   free  .   .
Thirsty Dice                        .   .   .   ?   ?         full_bar  Y   .   ?   Y   free  .   .
Cafe La Maude                       .   .   Y   2   average   none      .   Y   Y   Y   free  .   .
Hinge Cafe                          .   .   Y   2   average   none      .   .   Y   Y   free  .   .
Steap and Grind                     .   .   .   1   quiet     none      .   Y   Y   Y   free  .   .
La Colombe Coffee                   .   .   .   1   average   none      .   .   N   .   no    .   .
Last Drop                           .   .   .   1   quiet     none      .   .   Y   Y   free  .   .
Elixr Coffee Roasters               .   .   .   1   quiet     none      .   .   ?   .   free  .   Y
United By Blue                      .   .   .   2   average   none      .   Y   Y   Y   free  .   Y
Chapterhouse Cafe & Gallery         .   .   .   1   average   none      .   Y   N   Y   free  .   .
Sabrina's Cafe                      .   .   .   2   average   none      .   Y   Y   Y   free  .   .
```

### Unique Feature Combinations (for single-answer requests)

These combinations have exactly 1 matching restaurant:

| Combination | Restaurant |
|-------------|-----------|
| DriveThru=True | Milkcrate Cafe |
| Price=3 | Tria Cafe Rittenhouse |
| CoatCheck + FullBar | Front Street Cafe |
| Loud + NoOutdoor | Kung Fu Tea |
| Quiet + NoOutdoor | Swiss Haus Cafe |
| Dogs + Quiet | Steap and Grind |
| BYOB + Trendy | Function Coffee Labs |
| NoWiFi + NoOutdoor | La Colombe Coffee |
| Dogs + NoOutdoor | Chapterhouse Cafe |
| Quiet + Trendy | Elixr Coffee Roasters |
| CoatCheck + Dogs | Tria Cafe Rittenhouse |
| Loud + FullBar + Outdoor | MilkBoy |
| BeerWine + Quiet | Swiss Haus Cafe |
| Hipster + DriveThru | Milkcrate Cafe |
| Hipster + FullBar | Front Street Cafe |
| BYOB + Dogs + Hipster | Function Coffee Labs |
| Dogs + Trendy + Outdoor (not $3) | United By Blue |

---

## Review Selection

### Methodology

For each selected restaurant:
1. Sort reviews by date (newest first)
2. Take first 10 (most recent)
3. Sample from remaining reviews at regular intervals to get diversity
4. Total: 20 reviews per restaurant

```python
revs_sorted = sorted(revs, key=lambda x: x.get('date', ''), reverse=True)
selected_revs = revs_sorted[:10]  # Recent
remaining = revs_sorted[10:]
step = max(1, len(remaining) // 10)
for i in range(0, len(remaining), step):
    if len(selected_revs) >= 20:
        break
    selected_revs.append(remaining[i])
```

### Result
- 400 total reviews (20 x 20 restaurants)
- Mix of recent and older reviews
- Diverse star ratings within each restaurant

---

## Review Text Analysis

### Unique Keywords Found

We searched for keywords that appear in only 1-2 restaurants' reviews:

| Keyword | Restaurant(s) |
|---------|---------------|
| "live music" | MilkBoy (unique) |
| "gelato" | Gran Caffe L'Aquila (unique) |
| "wine bar" | Tria Cafe Rittenhouse (unique) |
| "wine list" | Tria Cafe Rittenhouse (unique) |
| "challah" | Sabrina's Cafe (unique) |
| "dog friendly" | Steap and Grind (unique) |
| "bring your dog" | Chapterhouse Cafe (unique) |
| "terrace" | Front Street Cafe (unique) |
| "late night" | Tria Cafe Rittenhouse (unique) |
| "midnight" | Thirsty Dice (unique) |
| "half price" | Front Street Cafe (unique) |
| "banh mi" | Front Street Cafe (unique) |
| "matcha latte" | United By Blue (unique) |
| "plant-based" | Front Street Cafe (unique) |
| "board game" | Thirsty Dice, Chapterhouse (2) |
| "bubble tea" | Kung Fu Tea, The Bubble House (2) |
| "boba" | Kung Fu Tea, The Bubble House (2) |
| "vietnamese" | The Bubble House (unique) |
| "latte art" | La Colombe, Elixr (2) |
| "green tea" | Kung Fu Tea, Chapterhouse (2) |

### Keywords NOT Unique (avoid for single-answer requests)

| Keyword | Count | Sample Restaurants |
|---------|-------|-------------------|
| "brunch" | 10+ | Many restaurants |
| "croissant" | 9 | Many restaurants |
| "wine" | 8 | Many restaurants |
| "vegan" | 5+ | Many restaurants |
| "books" | 6 | Multiple cafes |

---

## Request Design

### Design Principles

1. **Single Answer**: Each request must match exactly 1 restaurant
2. **Diverse Evidence**: Mix of metadata, review text, and combinations
3. **Natural Language**: Requests should sound like real user queries
4. **Scenarios**: Each request has a realistic user scenario

### Request Groups

#### G01: Simple Metadata (10 requests)
Single or paired attribute filters using `item_meta` evidence.

| ID | Target | Key Filter |
|----|--------|-----------|
| R00 | Milkcrate Cafe | DriveThru=True |
| R01 | Tria Cafe Rittenhouse | Price=3 |
| R02 | Front Street Cafe | CoatCheck + FullBar |
| R03 | Kung Fu Tea | Loud + NoOutdoor |
| R04 | Swiss Haus Cafe | Quiet + NoOutdoor |
| R05 | Steap and Grind | Dogs + Quiet |
| R06 | Function Coffee Labs | BYOB + Trendy |
| R07 | La Colombe Coffee | NoWiFi + NoOutdoor |
| R08 | Chapterhouse Cafe | Dogs + NoOutdoor |
| R09 | Elixr Coffee Roasters | Quiet + Trendy |

#### G02: Review Text (10 requests)
Unique keyword patterns using `review_text` evidence.

| ID | Target | Keyword |
|----|--------|---------|
| R10 | MilkBoy | "live music" |
| R11 | Gran Caffe L'Aquila | "gelato" |
| R12 | Tria Cafe Rittenhouse | "wine bar" |
| R13 | Sabrina's Cafe | "challah" |
| R14 | Steap and Grind | "dog friendly" |
| R15 | United By Blue | "matcha latte" |
| R16 | Thirsty Dice | "midnight" |
| R17 | Front Street Cafe | "banh mi" |
| R18 | Front Street Cafe | "terrace" |
| R19 | Chapterhouse Cafe | "bring your dog" |

#### G03: Complex Metadata (10 requests)
Multi-attribute combinations requiring 3+ filters.

| ID | Target | Combination |
|----|--------|-------------|
| R20 | Gran Caffe L'Aquila | FullBar + HappyHour + Outdoor |
| R21 | Le Pain Quotidien | HappyHour + Kids + Outdoor + NoAlcohol |
| R22 | Cafe La Maude | BYOB + Outdoor + Kids + Dogs + NotTrendy |
| R23 | MilkBoy | Loud + Outdoor + FullBar |
| R24 | Swiss Haus Cafe | BeerWine + Quiet |
| R25 | Tria Cafe Rittenhouse | CoatCheck + Dogs |
| R26 | Milkcrate Cafe | Hipster + DriveThru |
| R27 | The Bubble House | FullBar + Kids + WiFi + NoHappyHour |
| R28 | United By Blue | Dogs + Trendy + Outdoor + NotPrice3 |
| R29 | Thirsty Dice | FullBar + HappyHour + Kids + NoOutdoor |

#### G04: Social/Meta (10 requests)
Mixed evidence types combining metadata features.

| ID | Target | Combination |
|----|--------|-------------|
| R30 | Last Drop | Quiet + Outdoor |
| R31 | Front Street Cafe | Hipster + FullBar |
| R32 | Function Coffee Labs | Dogs + BYOB + Hipster |
| R33 | Sabrina's Cafe | Dogs + Outdoor + Kids + AverageNoise |
| R34 | Tria Cafe Rittenhouse | BeerWine + Trendy |
| R35 | Kung Fu Tea | Loud + WiFi |
| R36 | Hinge Cafe | BYOB + Outdoor + NoDogs |
| R37 | Steap and Grind | Price$1 + Quiet + WiFi + Dogs |
| R38 | MilkBoy | NoWiFi + Loud |
| R39 | The Bubble House | FullBar + Outdoor + NoHappyHour |

#### G05: Nested Logic (10 requests)
Review text + metadata combinations.

| ID | Target | Combination |
|----|--------|-------------|
| R40 | Tria Cafe Rittenhouse | "wine list" + CoatCheck |
| R41 | Thirsty Dice | "board game" + FullBar |
| R42 | Kung Fu Tea | "bubble tea" + Loud |
| R43 | The Bubble House | "vietnamese" + FullBar |
| R44 | Front Street Cafe | "half price" + Hipster |
| R45 | Steap and Grind | Quiet + Price$1 + Dogs + Outdoor |
| R46 | La Colombe Coffee | "latte art" + NoWiFi |
| R47 | Function Coffee Labs | BYOB + Trendy + Dogs |
| R48 | Chapterhouse Cafe | "green tea" + Dogs |
| R49 | Tria Cafe Rittenhouse | Price$3 + Dogs + Trendy |

### Request Structure Format

```json
{
  "id": "R00",
  "group": "G01",
  "scenario": "Busy Parent",
  "text": "I need a cafe with a drive-thru option - I can't get my kids out of the car",
  "structure": {
    "op": "AND",
    "args": [
      {
        "aspect": "drive_thru",
        "evidence": {
          "kind": "item_meta",
          "path": ["attributes", "DriveThru"],
          "true": "True"
        }
      }
    ]
  },
  "gold_restaurant": "e-ZyZc24wgkKafM3pguR2w"
}
```

### Evidence Types

| Kind | Description | Example |
|------|-------------|---------|
| `item_meta` | Restaurant attribute | `{"path": ["attributes", "WiFi"], "true": "u'free'"}` |
| `review_text` | Keyword in reviews | `{"pattern": "live music"}` |
| `item_meta` with `contains` | Dict attribute check | `{"contains": "'trendy': True"}` |
| `item_meta` with `not_true` | Negative check | `{"not_true": "True"}` |

---

## Gold Restaurant Distribution

Each of the 20 restaurants is used as a gold answer:

| Restaurant | # Requests |
|------------|-----------|
| Tria Cafe Rittenhouse | 6 |
| Front Street Cafe | 5 |
| Steap and Grind | 4 |
| Kung Fu Tea | 3 |
| Function Coffee Labs | 3 |
| Chapterhouse Cafe & Gallery | 3 |
| MilkBoy | 3 |
| Thirsty Dice | 3 |
| The Bubble House | 3 |
| Milkcrate Cafe | 2 |
| Swiss Haus Cafe & Pastry Bar | 2 |
| La Colombe Coffee | 2 |
| Gran Caffe L'Aquila | 2 |
| Sabrina's Cafe | 2 |
| United By Blue | 2 |
| Elixr Coffee Roasters | 1 |
| Le Pain Quotidien | 1 |
| Cafe La Maude | 1 |
| Last Drop | 1 |
| Hinge Cafe | 1 |

---

## Output Files

```
data/philly_cafes/
├── restaurants.jsonl   # 20 restaurants (33KB)
├── reviews.jsonl       # 400 reviews (3.8MB)
├── requests.jsonl      # 50 requests (23KB)
└── meta.json           # Dataset metadata (1.4KB)
```

---

## How to Expand/Adjust

### Adding More Restaurants

1. Run analysis on source data:
   ```bash
   python -m preprocessing.analyze philly_cafes
   ```

2. Check which features are underrepresented in current selection

3. Find restaurants with those features:
   ```python
   # In preprocessing/output/philly_cafes/restaurants.jsonl
   # Filter for: reviews >= 20 AND has_needed_feature
   ```

4. Add to selected_ids list and regenerate

### Adding More Requests

1. Identify unused unique combinations from Feature Matrix

2. Search for new unique keywords:
   ```python
   # Search pattern in reviews
   for keyword in new_keywords:
       matches = [r for r in restaurants if keyword in r['reviews']]
       if 1 <= len(matches) <= 2:
           print(f"'{keyword}': {matches}")
   ```

3. Create request with structure format

4. Verify single answer by checking all restaurants against criteria

### Adjusting Review Selection

Current selection prioritizes recency. To change:

```python
# For more diversity in ratings:
revs_by_stars = defaultdict(list)
for r in revs:
    revs_by_stars[r['stars']].append(r)
# Take proportionally from each star rating

# For elite reviewer priority:
elite_revs = [r for r in revs if r.get('user', {}).get('elite')]
```

### Validation Script

To verify all requests have exactly 1 answer:

```python
import json

def check_request(req, restaurants):
    """Return list of restaurants matching request criteria."""
    matches = []
    for r in restaurants:
        if matches_criteria(r, req['structure']):
            matches.append(r['name'])
    return matches

# Each should return exactly 1 match
for req in requests:
    matches = check_request(req, restaurants)
    assert len(matches) == 1, f"{req['id']}: {len(matches)} matches"
```

---

## Notes

- Attribute values in Yelp data use Python repr format: `"u'free'"`, `"'casual'"`, etc.
- Boolean attributes are strings: `"True"` or `"False"`
- Dict attributes (Ambience, BusinessParking) are string representations of dicts
- Some attributes may be missing (`None`) - handle in queries
- Hours use `"H:M-H:M"` format, `"0:0-0:0"` typically means closed that day

---

*Created: 2026-01-01*
*Source: preprocessing/output/philly_cafes/*
*Output: data/philly_cafes/*
