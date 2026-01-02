# xnot

Research framework for ANoT (Adaptive Network of Thought) - evaluating LLM prompting methods on structured multi-source data.

## Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Set API key (or place in ../.openaiapi)
export OPENAI_API_KEY="sk-..."
```

## Preprocessing

Curate restaurants from raw Yelp data:

```bash
# With LLM scoring (recommended)
python preprocessing/scripts/curate.py \
    --name philly_cafes \
    --city Philadelphia \
    --category "Coffee & Tea" Cafes

# Fast mode (heuristic scoring)
python preprocessing/scripts/curate.py \
    --name philly_bars \
    --city Philadelphia \
    --category Bars Nightlife \
    --skip-llm

# Analyze for ground truth design
python preprocessing/scripts/analyze.py philly_cafes
```

Output:
```
preprocessing/output/{name}/
├── restaurants.jsonl   # 100 restaurants with metadata
├── reviews.jsonl       # ALL reviews with user data
├── analysis.json       # Attribute distributions
└── meta.json           # Creation params
```

## Project Structure

```
xnot/
├── preprocessing/      # Data curation pipeline
│   ├── raw/            # Raw Yelp data (gitignored)
│   ├── scripts/        # curate.py, analyze.py
│   └── output/         # Curated selections
├── utils/              # Shared utilities (llm.py, io.py)
├── doc/                # Research documentation
├── data/               # Final curated data for experiments
├── scripts/            # Main experiment scripts
├── results/            # Experiment outputs
└── oldsrc/             # Legacy reference code
```

## Documentation

See `doc/` for research plan and evaluation protocol.
