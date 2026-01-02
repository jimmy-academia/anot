# Preprocessing Pipeline

This directory contains the preliminary data filtering workflow for creating curated restaurant selections from raw Yelp data.

## Directory Structure

```
preprocessing/
├── raw/                           # Raw Yelp academic dataset (gitignored)
│   ├── yelp_academic_dataset_business.json
│   ├── yelp_academic_dataset_review.json
│   └── yelp_academic_dataset_user.json
├── scripts/
│   ├── curate.py                  # Select restaurants from raw data
│   ├── sample_reviews.py          # Sample reviews per restaurant
│   └── analyze.py                 # Analyze data for GT constraint design
├── output/                        # Intermediate outputs
│   ├── selection_1.jsonl          # Selected restaurant IDs
│   ├── restaurants_cache_1.jsonl  # Restaurant metadata cache
│   ├── reviews_cache_1.jsonl      # Reviews cache with user metadata
│   └── analysis_results.json      # Analysis output
└── data_summary.md                # Human-readable analysis summary
```

## Workflow

```
Raw Yelp Data
    ↓
curate.py          →  selection_N.jsonl (restaurant IDs + LLM scores)
    ↓
sample_reviews.py  →  restaurants_cache_N.jsonl, reviews_cache_N.jsonl
    ↓
analyze.py         →  analysis_results.json, data_summary.md
    ↓
(Main pipeline in scripts/: curate.py, generate_requests.py, validate_gt.py)
```

## Usage

```bash
# 1. Curate restaurants (requires raw data)
python preprocessing/scripts/curate.py --city Philadelphia --category Restaurants

# 2. Sample reviews for selected restaurants
python preprocessing/scripts/sample_reviews.py selection_1

# 3. Analyze for GT constraint design
python preprocessing/scripts/analyze.py
```

## Notes

- Raw data files are large (5+ GB) and gitignored
- Cache files are the input to the main data pipeline
- Analysis helps identify unique attributes for ground truth filtering
