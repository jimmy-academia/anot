# Preprocessing Pipeline

Curate restaurants from raw Yelp data for ground truth constraint design.

## Structure

```
preprocessing/
├── raw/                    # Raw Yelp academic dataset (gitignored)
├── scripts/
│   ├── curate.py           # Curate restaurants + fetch ALL reviews
│   └── analyze.py          # Analyze for GT constraint design
├── output/
│   └── {name}/
│       ├── restaurants.jsonl   # 100 restaurants with metadata
│       ├── reviews.jsonl       # ALL reviews for those restaurants
│       ├── analysis.json
│       └── meta.json
└── data_summary.md
```

## Workflow

```
curate.py  →  {name}/restaurants.jsonl, {name}/reviews.jsonl, {name}/meta.json
analyze.py →  {name}/analysis.json
```

## Usage

```bash
# Curate 100 restaurants + all their reviews
python preprocessing/scripts/curate.py --name philly_cafes --city Philadelphia --category Cafes

# Analyze for GT constraint design
python preprocessing/scripts/analyze.py philly_cafes
```

## Current Selections

| Name | City | Categories | Restaurants | Reviews |
|------|------|------------|-------------|---------|
| philly_cafes | Philadelphia | Coffee & Tea, Cafes | 220 | 4,302 |
