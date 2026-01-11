"""
Scoring utilities for General ANoT evaluation.

Modules:
- auprc: Ordinal AUPRC scoring with primitive accuracy
- ground_truth: Deterministic GT computation from stored judgments
"""

from .auprc import (
    calculate_ordinal_auprc,
    print_report,
    CLASS_ORDER,
    DEFAULT_TOLERANCES_V2,
    compute_avg_primitive_accuracy,
)
from .ground_truth import compute_gt_for_k
