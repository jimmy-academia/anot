#!/usr/bin/env python3
"""
main.py - LLM evaluation for restaurant recommendation.

Entry point for running evaluations with different methods.
"""

import logging

from utils.arguments import parse_args
from utils.llm import config_llm
from utils.experiment import create_experiment
from utils.aggregate import aggregate_benchmark_runs, print_summary
from data.loader import load_dataset

from run import run_single, run_scaling_experiment


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s"
    )
    # Suppress verbose logs (must be after basicConfig)
    for logger_name in ["httpx", "httpcore", "openai", "httpx._client", "asyncio"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    return logging.getLogger(__name__)


def main():
    args = parse_args()
    log = setup_logging(args.verbose)
    config_llm(args)

    # Scaling experiment (default) vs single run (--candidates N)
    if args.candidates is None:
        run_scaling_experiment(args, log)
        return

    # Check if this is a partial run (--limit was specified)
    is_partial = args.limit is not None

    if args.benchmark:
        if is_partial:
            # Partial run: always run and merge into latest/target run
            experiment = create_experiment(args)
            print(f"\n{'='*60}")
            print(f"Partial run (--limit {args.limit})")
            print(f"{'='*60}")
            run_single(args, experiment, log)
        else:
            # Full benchmark mode: run_single handles resume via results_{n}.jsonl
            experiment = create_experiment(args)
            run_single(args, experiment, log)

            # Check for additional runs needed (args.auto)
            experiment = create_experiment(args)
            completed = experiment.get_completed_runs()
            needed = args.auto - completed

            if needed > 0:
                print(f"Running {needed} more run(s) (have {completed}, need {args.auto})")
                for i in range(needed):
                    print(f"\n{'='*60}")
                    print(f"Run {completed + i + 1} of {args.auto}")
                    print(f"{'='*60}")
                    experiment = create_experiment(args)
                    run_single(args, experiment, log)

        # Always aggregate at end (benchmark mode)
        summary = aggregate_benchmark_runs(args.method, args.data)
        print_summary(summary, show_details=True)

    else:
        # Dev mode: single run, no aggregation
        experiment = create_experiment(args)
        run_single(args, experiment, log)


if __name__ == "__main__":
    main()
