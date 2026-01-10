#!/usr/bin/env python3
"""
G1a: Peanut Allergy Safety Task

Semantic reasoning task for assessing restaurant safety for severe peanut allergies.
Uses deterministically computed GT from stored per-review LLM judgments.

GT Pipeline:
1. Keyword filtering identifies allergy-relevant reviews
2. LLM extracts per-review signals (incident_severity, account_type, safety_interaction)
3. Python formulas compute all aggregates deterministically

Formula Versions:
- V1: Original formula (~25 primitives, simple arithmetic)
- V2: Harder formula (~35 primitives, trust-adjusted, trajectory, interaction terms)

Dynamic GT per K:
- GT is computed from reviews 0 to K-1 only
- Ensures fair evaluation when testing with different context sizes
- See g1_gt_compute.py for computation details
"""

from dataclasses import dataclass
from typing import List, Any

# Default formula version for evaluation
DEFAULT_FORMULA_VERSION = "v1"


@dataclass
class TaskG1GroundTruth:
    """Ground truth for peanut allergy safety assessment (V1 formula).

    Primitives computed via explicit formulas from per-review semantic judgments.
    """
    # Layer 1: Incident Counts (from firsthand accounts only)
    n_total_incidents: int  # n_mild + n_moderate + n_severe

    # Layer 2: Derived Metrics
    incident_score: float  # (mild*2 + moderate*5 + severe*15)
    recency_decay: float  # 0.3-1.0 based on incident age
    credibility_factor: float  # Weight based on stars + useful votes

    # Layer 3: Final Outputs
    final_risk_score: float  # 0-20, clamped
    verdict: str  # "Low Risk", "High Risk", "Critical Risk"


@dataclass
class TaskG1GroundTruthV2:
    """Ground truth for peanut allergy safety assessment (V2 formula).

    V2 adds: trust score, trust-adjusted weights, trajectory, silence penalty.
    """
    # Layer 1: Counts
    n_total_incidents: int
    n_allergy_reviews: int

    # Layer 2: Trust Score (NEW in V2)
    trust_score: float  # 0.1-1.0

    # Layer 2: Trust-Adjusted (NEW in V2)
    adjusted_incident_score: float
    trajectory_multiplier: float  # 0.7, 1.0, or 1.3

    # Layer 2: Derived (same concept as V1)
    recency_decay: float
    credibility_factor: float
    cuisine_impact: float

    # Layer 3: Final (MODIFIED formula in V2)
    incident_impact: float
    trust_impact: float
    positive_credit: float
    final_risk_score: float
    verdict: str


# Dynamic GT computation - no static cache needed
# GT is computed on-demand for each K value using compute_gt_for_k()


def compute_task_g1_ground_truth(reviews: List[Any], restaurant: Any, k: int = None) -> TaskG1GroundTruth:
    """
    Compute G1a ground truth dynamically based on K.

    For fair evaluation across different context sizes, GT is computed from
    only the reviews that the model can see (reviews 0 to k-1).

    Args:
        reviews: List of reviews (used for fallback only)
        restaurant: Restaurant metadata dict
        k: Number of reviews model can see. If None, use all reviews.

    Returns:
        TaskG1GroundTruth computed from reviews 0 to k-1
    """
    from g1_gt_compute import compute_gt_for_k

    res_name = restaurant.get('name', 'Unknown')

    try:
        gt = compute_gt_for_k(res_name, k=k)
        return TaskG1GroundTruth(
            n_total_incidents=gt.n_total_incidents,
            incident_score=gt.incident_score,
            recency_decay=gt.recency_decay,
            credibility_factor=gt.credibility_factor,
            final_risk_score=gt.final_risk_score,
            verdict=gt.verdict
        )
    except ValueError:
        # Fallback for unknown restaurants
        return TaskG1GroundTruth(
            n_total_incidents=0,
            incident_score=0.0,
            recency_decay=1.0,
            credibility_factor=1.0,
            final_risk_score=2.75,  # BASE_RISK + CUISINE_IMPACT default
            verdict="Low Risk"
        )


TASK_G1_PROMPT = """Analyze the reviews for PEANUT/NUT ALLERGY SAFETY using the exact formulas below.

## STEP 1: Per-Review Semantic Extraction

For each review mentioning allergies, extract:

1. INCIDENT_SEVERITY: "none" | "mild" | "moderate" | "severe"
   - none: No allergic reaction described
   - mild: Minor symptoms (stomach upset, mild discomfort)
   - moderate: Visible symptoms (hives, swelling, needed medication)
   - severe: Life-threatening (anaphylaxis, EpiPen, ER visit, hospitalization)

2. ACCOUNT_TYPE: "none" | "firsthand" | "secondhand" | "hypothetical"
   - none: No incident
   - firsthand: Personal experience ("I had", "my child", "we experienced")
   - secondhand: Reported ("I heard", "friend told me")
   - hypothetical: Concern without incident

3. SAFETY_INTERACTION: "none" | "positive" | "negative" | "betrayal"
   - none: No staff interaction about allergies
   - positive: Staff asked about allergies AND successfully accommodated
   - negative: Staff dismissive or refused to accommodate
   - betrayal: Staff CLAIMED safe BUT customer still had a reaction

## STEP 2: Aggregate Counts (Firsthand Incidents Only)

N_MILD = Count reviews where (INCIDENT_SEVERITY="mild" AND ACCOUNT_TYPE="firsthand")
N_MODERATE = Count reviews where (INCIDENT_SEVERITY="moderate" AND ACCOUNT_TYPE="firsthand")
N_SEVERE = Count reviews where (INCIDENT_SEVERITY="severe" AND ACCOUNT_TYPE="firsthand")
N_TOTAL_INCIDENTS = N_MILD + N_MODERATE + N_SEVERE

N_POSITIVE = Count reviews where SAFETY_INTERACTION="positive"
N_NEGATIVE = Count reviews where SAFETY_INTERACTION="negative"
N_BETRAYAL = Count reviews where SAFETY_INTERACTION="betrayal"

## STEP 3: Calculate Derived Values

INCIDENT_SCORE = (N_MILD * 2) + (N_MODERATE * 5) + (N_SEVERE * 15)

SAFETY_CREDIT = (N_POSITIVE * 1.0) - (N_NEGATIVE * 0.5) - (N_BETRAYAL * 5.0)

CUISINE_MODIFIER = lookup restaurant categories:
  Thai=2.0, Vietnamese=1.8, Chinese=1.5, Asian=1.5,
  Indian=1.3, Japanese=1.2, Korean=1.2, Mexican=1.0,
  Italian=0.5, American=0.5, Pizza=0.5, default=1.0

N_ALLERGY_REVIEWS = Count reviews mentioning allergy-related terms
REVIEW_DENSITY = min(1.0, N_ALLERGY_REVIEWS / 10.0)
CONFIDENCE_PENALTY = 1.0 - (0.3 * (1 - REVIEW_DENSITY))

MOST_RECENT_INCIDENT_YEAR = max(year) from incident reviews (default: 2020)
INCIDENT_AGE = 2025 - MOST_RECENT_INCIDENT_YEAR
RECENCY_DECAY = max(0.3, 1.0 - (INCIDENT_AGE * 0.15))

For each incident review, calculate:
  WEIGHT = (5 - stars) + log(useful + 1)
TOTAL_INCIDENT_WEIGHT = sum(WEIGHT for incident reviews)
CREDIBILITY_FACTOR = TOTAL_INCIDENT_WEIGHT / max(N_TOTAL_INCIDENTS, 1)
  (default: 1.0 if no incidents)

## STEP 4: Final Score Calculation

BASE_RISK = 2.5

INCIDENT_IMPACT = INCIDENT_SCORE * RECENCY_DECAY * CREDIBILITY_FACTOR
SAFETY_IMPACT = SAFETY_CREDIT * CONFIDENCE_PENALTY
CUISINE_IMPACT = CUISINE_MODIFIER * 0.5

RAW_RISK = BASE_RISK + INCIDENT_IMPACT - SAFETY_IMPACT + CUISINE_IMPACT - (N_BETRAYAL * 3.0)

FINAL_RISK_SCORE = max(0.0, min(20.0, RAW_RISK))

VERDICT:
  If FINAL_RISK_SCORE < 4.0: "Low Risk"
  If 4.0 <= FINAL_RISK_SCORE < 8.0: "High Risk"
  If FINAL_RISK_SCORE >= 8.0: "Critical Risk"

## OUTPUT

Report all intermediate values and final answers."""


# V2 Prompt: Harder formula with trust, trajectory, and interaction terms
TASK_G1_PROMPT_V2 = """Analyze the reviews for PEANUT/NUT ALLERGY SAFETY using the exact formulas below.

## STEP 1: Per-Review Semantic Extraction

For each review mentioning allergies, extract:

1. INCIDENT_SEVERITY: "none" | "mild" | "moderate" | "severe"
   - none: No allergic reaction described
   - mild: Minor symptoms (stomach upset, mild discomfort)
   - moderate: Visible symptoms (hives, swelling, needed medication)
   - severe: Life-threatening (anaphylaxis, EpiPen, ER visit)

2. ACCOUNT_TYPE: "none" | "firsthand" | "secondhand" | "hypothetical"
   - firsthand: Personal experience ("I had", "my child experienced")
   - secondhand: Reported ("I heard", "friend told me")
   - hypothetical: Concern without incident

3. SAFETY_INTERACTION: "none" | "positive" | "negative" | "betrayal"
   - positive: Staff asked about allergies AND successfully accommodated
   - negative: Staff dismissive or refused to accommodate
   - betrayal: Staff CLAIMED safe BUT customer still had reaction

## STEP 2: Aggregate Counts

Count from FIRSTHAND accounts only:
  N_MILD = count(INCIDENT_SEVERITY="mild" AND ACCOUNT_TYPE="firsthand")
  N_MODERATE = count(INCIDENT_SEVERITY="moderate" AND ACCOUNT_TYPE="firsthand")
  N_SEVERE = count(INCIDENT_SEVERITY="severe" AND ACCOUNT_TYPE="firsthand")
  N_TOTAL_INCIDENTS = N_MILD + N_MODERATE + N_SEVERE

Count all safety interactions:
  N_POSITIVE = count(SAFETY_INTERACTION="positive")
  N_NEGATIVE = count(SAFETY_INTERACTION="negative")
  N_BETRAYAL = count(SAFETY_INTERACTION="betrayal")

Count allergy-relevant reviews:
  N_ALLERGY_REVIEWS = count(reviews mentioning allergy-related terms)

## STEP 3: Trust Score Calculation

Staff trust based on interaction history:
  TRUST_RAW = 1.0 + (N_POSITIVE * 0.1) - (N_NEGATIVE * 0.2) - (N_BETRAYAL * 0.5)
  TRUST_SCORE = max(0.1, min(1.0, TRUST_RAW))

Interpretation:
  - TRUST_SCORE near 1.0 = reliable staff
  - TRUST_SCORE near 0.1 = untrustworthy (betrayals or many negatives)

## STEP 4: Severity Weights (Trust-Adjusted)

Severity weights depend on trust level:
  MILD_WEIGHT = 2 * (1.5 - TRUST_SCORE)
  MODERATE_WEIGHT = 5 * (1.3 - 0.3 * TRUST_SCORE)
  SEVERE_WEIGHT = 15

Calculate adjusted incident score:
  ADJUSTED_INCIDENT_SCORE = (N_MILD * MILD_WEIGHT) + (N_MODERATE * MODERATE_WEIGHT) + (N_SEVERE * SEVERE_WEIGHT)

## STEP 5: Temporal Trajectory

Separate incidents by time:
  N_RECENT = count(incidents where review_year >= 2023)
  N_OLD = count(incidents where review_year < 2023)

Calculate trajectory:
  If N_TOTAL_INCIDENTS > 0:
    RECENT_RATIO = N_RECENT / N_TOTAL_INCIDENTS
  Else:
    RECENT_RATIO = 0

Determine trajectory multiplier:
  If RECENT_RATIO > 0.7:
    TRAJECTORY_MULTIPLIER = 1.3    # Getting worse
  Else if RECENT_RATIO < 0.3 AND N_TOTAL_INCIDENTS > 0:
    TRAJECTORY_MULTIPLIER = 0.7    # Improving
  Else:
    TRAJECTORY_MULTIPLIER = 1.0    # Stable

## STEP 6: Cuisine Risk

Lookup cuisine modifier:
  Thai=2.0, Vietnamese=1.8, Chinese=1.5, Asian Fusion=1.5,
  Indian=1.3, Japanese=1.2, Korean=1.2, Mexican=1.0,
  Italian=0.5, American=0.5, Pizza=0.5, default=1.0

  CUISINE_MODIFIER = highest matching value from restaurant categories

Silence penalty (high-risk cuisine with no allergy discussion):
  If N_ALLERGY_REVIEWS == 0:
    SILENCE_PENALTY = CUISINE_MODIFIER * 0.5
  Else:
    SILENCE_PENALTY = 0

  CUISINE_IMPACT = (CUISINE_MODIFIER * 0.5) + SILENCE_PENALTY

## STEP 7: Recency Decay

Find most recent incident year:
  If N_TOTAL_INCIDENTS > 0:
    MOST_RECENT_YEAR = max(review_year for incident reviews)
  Else:
    MOST_RECENT_YEAR = 2020

  INCIDENT_AGE = 2025 - MOST_RECENT_YEAR
  RECENCY_DECAY = max(0.3, 1.0 - (INCIDENT_AGE * 0.15))

## STEP 8: Credibility Factor

For each incident review, calculate weight:
  WEIGHT = (5 - stars) + log(useful_votes + 1)

Aggregate:
  TOTAL_WEIGHT = sum(WEIGHT for all incident reviews)
  If N_TOTAL_INCIDENTS > 0:
    CREDIBILITY_FACTOR = TOTAL_WEIGHT / N_TOTAL_INCIDENTS
  Else:
    CREDIBILITY_FACTOR = 1.0

## STEP 9: Final Score Calculation

Calculate component impacts:
  INCIDENT_IMPACT = ADJUSTED_INCIDENT_SCORE * TRAJECTORY_MULTIPLIER * RECENCY_DECAY * CREDIBILITY_FACTOR
  TRUST_IMPACT = (1.0 - TRUST_SCORE) * 3.0
  POSITIVE_CREDIT = N_POSITIVE * TRUST_SCORE * 0.5

Combine:
  BASE_RISK = 2.0
  RAW_RISK = BASE_RISK + INCIDENT_IMPACT + TRUST_IMPACT + CUISINE_IMPACT - POSITIVE_CREDIT

Clamp:
  FINAL_RISK_SCORE = max(0.0, min(20.0, RAW_RISK))

## STEP 10: Verdict

  If FINAL_RISK_SCORE < 4.0: VERDICT = "Low Risk"
  If 4.0 <= FINAL_RISK_SCORE < 8.0: VERDICT = "High Risk"
  If FINAL_RISK_SCORE >= 8.0: VERDICT = "Critical Risk"

## OUTPUT

Report ALL intermediate values:
  N_MILD, N_MODERATE, N_SEVERE, N_TOTAL_INCIDENTS
  N_POSITIVE, N_NEGATIVE, N_BETRAYAL
  N_ALLERGY_REVIEWS
  TRUST_SCORE
  MILD_WEIGHT, MODERATE_WEIGHT, ADJUSTED_INCIDENT_SCORE
  N_RECENT, N_OLD, RECENT_RATIO, TRAJECTORY_MULTIPLIER
  CUISINE_MODIFIER, SILENCE_PENALTY, CUISINE_IMPACT
  RECENCY_DECAY, CREDIBILITY_FACTOR
  INCIDENT_IMPACT, TRUST_IMPACT, POSITIVE_CREDIT
  RAW_RISK, FINAL_RISK_SCORE, VERDICT"""


TASK_G1_TOLERANCES = {
    'n_total_incidents': 0,  # Exact count
    'incident_score': 0,  # Exact calculation
    'recency_decay': 0.1,  # Float tolerance
    'credibility_factor': 0.2,  # Float tolerance
    'final_risk_score': 1.5,  # Score tolerance
}


TASK_G1_TOLERANCES_V2 = {
    'n_total_incidents': 0,  # Exact count
    'n_allergy_reviews': 0,  # Exact count
    'trust_score': 0.1,  # Float tolerance
    'adjusted_incident_score': 1.0,  # More complex calculation
    'trajectory_multiplier': 0,  # Exact (0.7, 1.0, or 1.3)
    'recency_decay': 0.1,  # Float tolerance
    'credibility_factor': 0.2,  # Float tolerance
    'cuisine_impact': 0.2,  # Float tolerance
    'incident_impact': 2.0,  # More complex, larger tolerance
    'trust_impact': 0.3,  # Float tolerance
    'positive_credit': 0.2,  # Float tolerance
    'final_risk_score': 1.5,  # Score tolerance
}


def compute_task_g1_ground_truth_v2(reviews: List[Any], restaurant: Any, k: int = None) -> TaskG1GroundTruthV2:
    """
    Compute G1a ground truth using V2 formula.

    Args:
        reviews: List of reviews (used for fallback only)
        restaurant: Restaurant metadata dict
        k: Number of reviews model can see. If None, use all reviews.

    Returns:
        TaskG1GroundTruthV2 computed from reviews 0 to k-1
    """
    from g1_gt_compute import compute_gt_for_k

    res_name = restaurant.get('name', 'Unknown')

    try:
        gt = compute_gt_for_k(res_name, k=k, version="v2")
        return TaskG1GroundTruthV2(
            n_total_incidents=gt.n_total_incidents,
            n_allergy_reviews=gt.n_allergy_reviews,
            trust_score=gt.trust_score,
            adjusted_incident_score=gt.adjusted_incident_score,
            trajectory_multiplier=gt.trajectory_multiplier,
            recency_decay=gt.recency_decay,
            credibility_factor=gt.credibility_factor,
            cuisine_impact=gt.cuisine_impact,
            incident_impact=gt.incident_impact,
            trust_impact=gt.trust_impact,
            positive_credit=gt.positive_credit,
            final_risk_score=gt.final_risk_score,
            verdict=gt.verdict
        )
    except ValueError:
        # Fallback for unknown restaurants
        return TaskG1GroundTruthV2(
            n_total_incidents=0,
            n_allergy_reviews=0,
            trust_score=1.0,
            adjusted_incident_score=0.0,
            trajectory_multiplier=1.0,
            recency_decay=0.3,
            credibility_factor=1.0,
            cuisine_impact=0.5,
            incident_impact=0.0,
            trust_impact=0.0,
            positive_credit=0.0,
            final_risk_score=2.5,
            verdict="Low Risk"
        )


# Task Registry
TASK_REGISTRY = {
    'G1a': {
        'name': 'Peanut Allergy Safety (V1)',
        'version': 'v1',
        'ground_truth_class': TaskG1GroundTruth,
        'compute_ground_truth': compute_task_g1_ground_truth,
        'prompt': TASK_G1_PROMPT,
        'tolerances': TASK_G1_TOLERANCES,
        'scoring_fields': [
            'n_total_incidents',
            'incident_score',
            'recency_decay',
            'credibility_factor',
            'final_risk_score'
        ],
    },
    'G1a-v2': {
        'name': 'Peanut Allergy Safety (V2 - Harder)',
        'version': 'v2',
        'ground_truth_class': TaskG1GroundTruthV2,
        'compute_ground_truth': compute_task_g1_ground_truth_v2,
        'prompt': TASK_G1_PROMPT_V2,
        'tolerances': TASK_G1_TOLERANCES_V2,
        'scoring_fields': [
            'n_total_incidents',
            'trust_score',
            'adjusted_incident_score',
            'trajectory_multiplier',
            'recency_decay',
            'credibility_factor',
            'cuisine_impact',
            'incident_impact',
            'trust_impact',
            'positive_credit',
            'final_risk_score'
        ],
    },
}


def get_task(task_id: str) -> dict:
    """Get task configuration by ID."""
    if task_id not in TASK_REGISTRY:
        raise ValueError(f"Unknown task: {task_id}. Available: {list(TASK_REGISTRY.keys())}")
    return TASK_REGISTRY[task_id]


def list_tasks() -> List[str]:
    """List all available task IDs."""
    return list(TASK_REGISTRY.keys())
