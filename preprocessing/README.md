# Preprocessing Pipeline

This directory contains the preliminary data filtering workflow for creating curated restaurant selections from raw Yelp data.

## Directory Structure

```
preprocessing/
├── raw/                              # Raw Yelp academic dataset (gitignored)
│   ├── yelp_academic_dataset_business.json
│   ├── yelp_academic_dataset_review.json
│   └── yelp_academic_dataset_user.json
├── scripts/
│   ├── curate.py                     # Select restaurants from raw data
│   ├── sample_reviews.py             # Sample reviews per restaurant
│   └── analyze.py                    # Analyze data for GT constraint design
├── output/
│   └── {selection_name}/             # One directory per selection
│       ├── selection.jsonl           # Restaurant IDs + LLM scores
│       ├── restaurants.jsonl         # Restaurant metadata cache
│       ├── reviews.jsonl             # Reviews cache with user data
│       ├── analysis.json             # Analysis results
│       └── meta.json                 # Creation params + stats
├── data_summary.md                   # Human-readable analysis summary
└── README.md
```

## Naming Convention

Each selection gets a semantic directory name (e.g., `philly_cafes`) instead of numeric IDs.

**meta.json** captures creation parameters for reproducibility:
```json
{
  "name": "philly_cafes",
  "city": "Philadelphia",
  "categories": ["Coffee & Tea", "Cafes"],
  "created": "2024-12-31",
  "params": {"target": 100, "threshold": 70},
  "stats": {"restaurants": 220, "reviews": 4302}
}
```

## Workflow

```
Raw Yelp Data
    ↓
curate.py          →  {name}/selection.jsonl
    ↓
sample_reviews.py  →  {name}/restaurants.jsonl, {name}/reviews.jsonl
    ↓
analyze.py         →  {name}/analysis.json
    ↓
(Main pipeline uses output as input)
```

## Usage

```bash
# 1. Curate restaurants (requires raw data)
python preprocessing/scripts/curate.py --name philly_cafes --city Philadelphia --category Cafes

# 2. Sample reviews for selected restaurants
python preprocessing/scripts/sample_reviews.py philly_cafes

# 3. Analyze for GT constraint design
python preprocessing/scripts/analyze.py philly_cafes
```

## Current Selections

| Name | City | Categories | Restaurants | Reviews |
|------|------|------------|-------------|---------|
| philly_cafes | Philadelphia | Coffee & Tea, Cafes | 220 | 4,302 |

## Notes

- Raw data files are large (5+ GB) and gitignored
- Each selection is self-contained in its own directory
- Analysis helps identify unique attributes for ground truth filtering
