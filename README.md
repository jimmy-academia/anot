# anot

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
# Interactive mode (recommended)
python -m preprocessing.curate

# Non-interactive with CLI args
python -m preprocessing.curate \
    --name philly_cafes \
    --city Philadelphia \
    --category "Coffee & Tea" Cafes

# Analyze for ground truth design
python -m preprocessing.analyze philly_cafes
```

Output:
```
preprocessing/output/{name}/
├── restaurants.jsonl   # Restaurants with LLM scores
├── reviews.jsonl       # All reviews with user data
├── analysis.json       # Attribute distributions
└── meta.json           # Creation params
```

## Project Structure

```
anot/
├── preprocessing/      # Data curation pipeline
│   ├── curate.py       # Interactive curation tool
│   ├── analyze.py      # Analysis for GT design
│   ├── raw/            # Raw Yelp data (gitignored)
│   └── output/         # Curated selections
├── utils/              # Shared utilities (llm.py)
├── doc/                # Research documentation
├── data/               # Final curated data for experiments
├── results/            # Experiment outputs
└── oldsrc/             # Legacy reference code
```

## Documentation

See `doc/` for research plan and evaluation protocol.
