#!/usr/bin/env python3
"""LLM evaluation for restaurant recommendation dataset."""

from utils.arguments import parse_args
from utils.logger import setup_logger_level, logger
from utils.llm import config_llm
from utils.experiment import create_experiment, ExperimentError

from data.loader import load_data, load_requests
from methods import get_method

from run import get_attacks_list, run_evaluation_loop, save_final_config

def main():
    args = parse_args()
    logger = setup_logger_level(args.verbose)
    config_llm(args)

    # Create experiment (handles dev vs benchmark mode)
    experiment = create_experiment(args)
    run_dir = experiment.setup()

    mode_str = "BENCHMARK" if experiment.benchmark_mode else "development"
    logger.info(f"Mode: {mode_str}")
    logger.info(f"Run directory: {run_dir}")

    # Load data and requests
    items_clean = load_data(args.data, args.limit)
    requests = load_requests(args.requests)

    logger.info(f"Loaded {len(items_clean)} items from {args.data}")
    logger.info(f"Loaded {len(requests)} requests")

    # Select method and prepare attacks
    method = get_method(args, run_dir)
    attacks = get_attacks_list(args)

    # Run evaluation (handles both parallel and sequential)
    stats = run_evaluation_loop(args, items_clean, requests, method, attacks, experiment)

    # Finalize
    save_final_config(args, attacks, stats, experiment)
    experiment.consolidate_debug_logs()

if __name__ == "__main__":
    main()
