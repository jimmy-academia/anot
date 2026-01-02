# Preprocessing

Curate restaurants from raw Yelp data with interactive selection and LLM-assisted scoring.

## Structure

```
preprocessing/
├── curate.py              # Interactive curation tool
├── analyze.py             # Analysis for GT constraint design
├── raw/                   # Raw Yelp academic dataset (gitignored)
├── output/                # Curated selections
│   └── {name}/
│       ├── restaurants.jsonl
│       ├── reviews.jsonl
│       ├── analysis.json
│       └── meta.json
└── README.md
```

## Usage

```bash
# Interactive mode (default)
python -m preprocessing.curate

# Non-interactive with CLI args
python -m preprocessing.curate \
    --name philly_cafes \
    --city Philadelphia \
    --category "Coffee & Tea" Cafes

# Analyze selection
python -m preprocessing.analyze philly_cafes
```

## Interactive Mode

1. **City selection** - Paginated list with search
2. **Category selection** - Multi-select (e.g., `1,3,5`)
3. **Mode selection**:
   - **Auto**: LLM batch scoring, keeps restaurants above threshold
   - **Manual**: Review each restaurant one by one

## Output

| File | Description |
|------|-------------|
| `restaurants.jsonl` | Curated restaurants with LLM scores |
| `reviews.jsonl` | All reviews with user metadata |
| `analysis.json` | Attribute distributions |
| `meta.json` | Selection parameters |
