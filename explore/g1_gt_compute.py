#!/usr/bin/env python3
"""
Deterministic Ground Truth Computation for G1a (Peanut Allergy Safety)

Computes GT values from stored per-review judgments using explicit formulas.
NO LLM calls - pure arithmetic on stored semantic judgments.

Supports:
- Dynamic K: GT is computed only from reviews 0 to K-1
- Formula versions: v1 (simple) and v2 (trust-adjusted, harder)

Usage:
    # Compute GT for one restaurant (all reviews, default version)
    from g1_gt_compute import compute_gt_for_k
    gt = compute_gt_for_k("Restaurant Name")  # K=None means all

    # Compute GT for K=50 reviews only
    gt = compute_gt_for_k("Restaurant Name", k=50)

    # Compute GT with V2 formula (harder)
    gt = compute_gt_for_k("Restaurant Name", version="v2")

    # Compute all and save
    python g1_gt_compute.py --save
    python g1_gt_compute.py --save --version v2  # Save GT with V2 formula
"""

# Formula version: "v1" (original) or "v2" (harder with trust, trajectory, logic)
DEFAULT_FORMULA_VERSION = "v1"

import json
import math
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

DATA_DIR = Path(__file__).parent / "data"
JUDGMENTS_FILE = DATA_DIR / "semantic_gt" / "task_G1a" / "judgments.json"
OUTPUT_FILE = DATA_DIR / "semantic_gt" / "task_G1a" / "computed_gt.json"

# Cuisine risk modifiers (peanut/nut usage prevalence)
CUISINE_RISK_BASE = {
    "Thai": 2.0,
    "Vietnamese": 1.8,
    "Chinese": 1.5,
    "Asian Fusion": 1.5,
    "Indian": 1.3,
    "Japanese": 1.2,
    "Korean": 1.2,
    "Mexican": 1.0,
    "Italian": 0.5,
    "American (Traditional)": 0.5,
    "American (New)": 0.5,
    "Pizza": 0.5,
    "Sandwiches": 0.5,
    "Breakfast & Brunch": 0.6,
    "default": 1.0
}


@dataclass
class G1GroundTruth:
    """All GT primitives for G1.1 V1 - deterministically computed."""
    # Layer 1 Aggregates
    n_mild: int
    n_moderate: int
    n_severe: int
    n_total_incidents: int
    n_positive: int
    n_negative: int
    n_betrayal: int

    # Layer 2 Derived
    incident_score: float
    safety_credit: float
    cuisine_modifier: float
    n_allergy_reviews: int
    review_density: float
    confidence_penalty: float
    most_recent_incident_year: int
    incident_age: int
    recency_decay: float
    total_incident_weight: float
    credibility_factor: float

    # Layer 3 Final
    incident_impact: float
    safety_impact: float
    cuisine_impact: float
    raw_risk: float
    final_risk_score: float
    verdict: str


@dataclass
class G1GroundTruthV2:
    """All GT primitives for G1.1 V2 - with trust, trajectory, and logic operators."""
    # Layer 1 Aggregates (same as V1)
    n_mild: int
    n_moderate: int
    n_severe: int
    n_total_incidents: int
    n_positive: int
    n_negative: int
    n_betrayal: int
    n_allergy_reviews: int

    # Layer 2: Trust Score (NEW in V2)
    trust_raw: float
    trust_score: float

    # Layer 2: Trust-Adjusted Weights (NEW in V2)
    mild_weight: float
    moderate_weight: float
    severe_weight: float  # Always 15
    adjusted_incident_score: float

    # Layer 2: Temporal Trajectory (NEW in V2)
    n_recent: int  # incidents where year >= 2023
    n_old: int     # incidents where year < 2023
    recent_ratio: float
    trajectory_multiplier: float  # 1.3 (worsening), 0.7 (improving), 1.0 (stable)

    # Layer 2: Cuisine with Silence Penalty (ENHANCED in V2)
    cuisine_modifier: float
    silence_penalty: float  # NEW: penalty when high-risk cuisine has no allergy mentions
    cuisine_impact: float

    # Layer 2: Recency and Credibility (same as V1)
    most_recent_incident_year: int
    incident_age: int
    recency_decay: float
    total_incident_weight: float
    credibility_factor: float

    # Layer 3: Final Score Components (MODIFIED in V2)
    incident_impact: float
    trust_impact: float      # NEW: (1 - trust_score) * 3.0
    positive_credit: float   # NEW: n_positive * trust_score * 0.5
    raw_risk: float
    final_risk_score: float
    verdict: str


def get_cuisine_modifier(categories: str) -> float:
    """Extract highest-risk cuisine modifier from category string."""
    cats = [c.strip() for c in categories.split(",")]
    max_risk = CUISINE_RISK_BASE["default"]
    for cat in cats:
        if cat in CUISINE_RISK_BASE:
            max_risk = max(max_risk, CUISINE_RISK_BASE[cat])
    return max_risk


def compute_gt_from_data(data: Dict) -> G1GroundTruth:
    """
    Compute all GT primitives from judgment data for one restaurant.
    This is DETERMINISTIC - no LLM calls, just arithmetic.

    Args:
        data: Restaurant judgment data with 'restaurant_meta' and 'reviews' keys

    Returns:
        G1GroundTruth dataclass with all computed primitives
    """
    reviews = data.get("reviews", [])
    categories = data.get("restaurant_meta", {}).get("categories", "")

    # === LAYER 1: Count from per-review judgments ===
    n_mild = n_moderate = n_severe = 0
    n_positive = n_negative = n_betrayal = 0
    n_allergy_reviews = 0
    incident_reviews = []  # For credibility calculation

    for r in reviews:
        # All judged reviews are allergy-relevant (they matched keywords)
        n_allergy_reviews += 1

        severity = r.get("incident_severity", "none")
        account = r.get("account_type", "none")
        interaction = r.get("safety_interaction", "none")

        # Count incidents (firsthand only)
        if account == "firsthand":
            if severity == "mild":
                n_mild += 1
                incident_reviews.append(r)
            elif severity == "moderate":
                n_moderate += 1
                incident_reviews.append(r)
            elif severity == "severe":
                n_severe += 1
                incident_reviews.append(r)

        # Count safety interactions
        if interaction == "positive":
            n_positive += 1
        elif interaction == "negative":
            n_negative += 1
        elif interaction == "betrayal":
            n_betrayal += 1

    n_total_incidents = n_mild + n_moderate + n_severe

    # === LAYER 2: Compute derived values ===

    # Step 2.3: Incident Score
    incident_score = float((n_mild * 2) + (n_moderate * 5) + (n_severe * 15))

    # Step 2.4: Safety Credit
    safety_credit = (n_positive * 1.0) - (n_negative * 0.5) - (n_betrayal * 5.0)

    # Step 2.5: Cuisine Modifier
    cuisine_modifier = get_cuisine_modifier(categories)

    # Step 2.6: Review Density & Confidence
    review_density = min(1.0, n_allergy_reviews / 10.0)
    confidence_penalty = 1.0 - (0.3 * (1 - review_density))

    # Step 2.7: Recency
    if incident_reviews:
        years = []
        for r in incident_reviews:
            date_str = r.get("date", "2020-01-01")
            try:
                year = int(date_str[:4])
            except (ValueError, TypeError):
                year = 2020
            years.append(year)
        most_recent_incident_year = max(years)
    else:
        most_recent_incident_year = 2020  # Default old

    incident_age = 2025 - most_recent_incident_year
    recency_decay = max(0.3, 1.0 - (incident_age * 0.15))

    # Step 2.8: Credibility Factor
    if incident_reviews:
        total_weight = 0.0
        for r in incident_reviews:
            stars = r.get("stars", 3)
            useful = r.get("useful", 0)
            weight = (5 - stars) + math.log(useful + 1)
            total_weight += weight
        credibility_factor = total_weight / max(n_total_incidents, 1)
    else:
        total_weight = 0.0
        credibility_factor = 1.0

    # === LAYER 3: Final Score ===
    BASE_RISK = 2.5

    incident_impact = incident_score * recency_decay * credibility_factor
    safety_impact = safety_credit * confidence_penalty
    cuisine_impact = cuisine_modifier * 0.5

    raw_risk = (BASE_RISK
                + incident_impact
                - safety_impact
                + cuisine_impact
                - (n_betrayal * 3.0))  # Extra penalty for false assurance

    final_risk_score = max(0.0, min(20.0, raw_risk))

    # Verdict
    if final_risk_score < 4.0:
        verdict = "Low Risk"
    elif final_risk_score < 8.0:
        verdict = "High Risk"
    else:
        verdict = "Critical Risk"

    return G1GroundTruth(
        n_mild=n_mild,
        n_moderate=n_moderate,
        n_severe=n_severe,
        n_total_incidents=n_total_incidents,
        n_positive=n_positive,
        n_negative=n_negative,
        n_betrayal=n_betrayal,
        incident_score=incident_score,
        safety_credit=safety_credit,
        cuisine_modifier=cuisine_modifier,
        n_allergy_reviews=n_allergy_reviews,
        review_density=review_density,
        confidence_penalty=round(confidence_penalty, 3),
        most_recent_incident_year=most_recent_incident_year,
        incident_age=incident_age,
        recency_decay=round(recency_decay, 3),
        total_incident_weight=round(total_weight, 3),
        credibility_factor=round(credibility_factor, 3),
        incident_impact=round(incident_impact, 3),
        safety_impact=round(safety_impact, 3),
        cuisine_impact=round(cuisine_impact, 3),
        raw_risk=round(raw_risk, 3),
        final_risk_score=round(final_risk_score, 2),
        verdict=verdict
    )


def compute_gt_from_data_v2(data: Dict) -> G1GroundTruthV2:
    """
    Compute all GT primitives using V2 formula (harder).

    V2 additions:
    - Trust Score based on safety interactions
    - Trust-adjusted severity weights
    - Temporal trajectory classification (improving/stable/worsening)
    - Cuisine silence penalty
    - Modified final score formula with trust impact and positive credit

    Args:
        data: Restaurant judgment data with 'restaurant_meta' and 'reviews' keys

    Returns:
        G1GroundTruthV2 dataclass with all computed primitives
    """
    reviews = data.get("reviews", [])
    categories = data.get("restaurant_meta", {}).get("categories", "")

    # === LAYER 1: Count from per-review judgments ===
    n_mild = n_moderate = n_severe = 0
    n_positive = n_negative = n_betrayal = 0
    n_allergy_reviews = 0
    incident_reviews = []  # For credibility calculation

    for r in reviews:
        n_allergy_reviews += 1

        severity = r.get("incident_severity", "none")
        account = r.get("account_type", "none")
        interaction = r.get("safety_interaction", "none")

        # Count incidents (firsthand only)
        if account == "firsthand":
            if severity == "mild":
                n_mild += 1
                incident_reviews.append(r)
            elif severity == "moderate":
                n_moderate += 1
                incident_reviews.append(r)
            elif severity == "severe":
                n_severe += 1
                incident_reviews.append(r)

        # Count safety interactions
        if interaction == "positive":
            n_positive += 1
        elif interaction == "negative":
            n_negative += 1
        elif interaction == "betrayal":
            n_betrayal += 1

    n_total_incidents = n_mild + n_moderate + n_severe

    # === LAYER 2: Trust Score Calculation (NEW in V2) ===
    # TRUST_RAW = 1.0 + (N_POSITIVE × 0.1) - (N_NEGATIVE × 0.2) - (N_BETRAYAL × 0.5)
    trust_raw = 1.0 + (n_positive * 0.1) - (n_negative * 0.2) - (n_betrayal * 0.5)
    trust_score = max(0.1, min(1.0, trust_raw))

    # === LAYER 2: Trust-Adjusted Severity Weights (NEW in V2) ===
    # MILD_WEIGHT = 2 × (1.5 - TRUST_SCORE)
    # MODERATE_WEIGHT = 5 × (1.3 - 0.3 × TRUST_SCORE)
    # SEVERE_WEIGHT = 15
    mild_weight = 2 * (1.5 - trust_score)
    moderate_weight = 5 * (1.3 - 0.3 * trust_score)
    severe_weight = 15.0

    # ADJUSTED_INCIDENT_SCORE = (N_MILD × MILD_WEIGHT) + (N_MODERATE × MODERATE_WEIGHT) + (N_SEVERE × SEVERE_WEIGHT)
    adjusted_incident_score = (n_mild * mild_weight) + (n_moderate * moderate_weight) + (n_severe * severe_weight)

    # === LAYER 2: Temporal Trajectory (NEW in V2) ===
    n_recent = 0  # incidents where year >= 2023
    n_old = 0     # incidents where year < 2023

    for r in incident_reviews:
        date_str = r.get("date", "2020-01-01")
        try:
            year = int(date_str[:4])
        except (ValueError, TypeError):
            year = 2020
        if year >= 2023:
            n_recent += 1
        else:
            n_old += 1

    # Calculate trajectory
    if n_total_incidents > 0:
        recent_ratio = n_recent / n_total_incidents
    else:
        recent_ratio = 0.0

    # Determine trajectory multiplier
    # If RECENT_RATIO > 0.7: TRAJECTORY_MULTIPLIER = 1.3 (Getting worse)
    # Else if RECENT_RATIO < 0.3 AND N_TOTAL_INCIDENTS > 0: TRAJECTORY_MULTIPLIER = 0.7 (Improving)
    # Else: TRAJECTORY_MULTIPLIER = 1.0 (Stable)
    if recent_ratio > 0.7:
        trajectory_multiplier = 1.3
    elif recent_ratio < 0.3 and n_total_incidents > 0:
        trajectory_multiplier = 0.7
    else:
        trajectory_multiplier = 1.0

    # === LAYER 2: Cuisine with Silence Penalty (ENHANCED in V2) ===
    cuisine_modifier = get_cuisine_modifier(categories)

    # Silence penalty: high-risk cuisine with no allergy discussion
    # If N_ALLERGY_REVIEWS == 0: SILENCE_PENALTY = CUISINE_MODIFIER × 0.5
    if n_allergy_reviews == 0:
        silence_penalty = cuisine_modifier * 0.5
    else:
        silence_penalty = 0.0

    cuisine_impact = (cuisine_modifier * 0.5) + silence_penalty

    # === LAYER 2: Recency Decay (same as V1) ===
    if incident_reviews:
        years = []
        for r in incident_reviews:
            date_str = r.get("date", "2020-01-01")
            try:
                year = int(date_str[:4])
            except (ValueError, TypeError):
                year = 2020
            years.append(year)
        most_recent_incident_year = max(years)
    else:
        most_recent_incident_year = 2020

    incident_age = 2025 - most_recent_incident_year
    recency_decay = max(0.3, 1.0 - (incident_age * 0.15))

    # === LAYER 2: Credibility Factor (same as V1) ===
    if incident_reviews:
        total_weight = 0.0
        for r in incident_reviews:
            stars = r.get("stars", 3)
            useful = r.get("useful", 0)
            weight = (5 - stars) + math.log(useful + 1)
            total_weight += weight
        credibility_factor = total_weight / max(n_total_incidents, 1)
    else:
        total_weight = 0.0
        credibility_factor = 1.0

    # === LAYER 3: Final Score Calculation (MODIFIED in V2) ===
    BASE_RISK = 2.0  # Slightly lower than V1's 2.5

    # INCIDENT_IMPACT = ADJUSTED_INCIDENT_SCORE × TRAJECTORY_MULTIPLIER × RECENCY_DECAY × CREDIBILITY_FACTOR
    incident_impact = adjusted_incident_score * trajectory_multiplier * recency_decay * credibility_factor

    # TRUST_IMPACT = (1.0 - TRUST_SCORE) × 3.0
    trust_impact = (1.0 - trust_score) * 3.0

    # POSITIVE_CREDIT = N_POSITIVE × TRUST_SCORE × 0.5
    positive_credit = n_positive * trust_score * 0.5

    # RAW_RISK = BASE_RISK + INCIDENT_IMPACT + TRUST_IMPACT + CUISINE_IMPACT - POSITIVE_CREDIT
    raw_risk = BASE_RISK + incident_impact + trust_impact + cuisine_impact - positive_credit

    final_risk_score = max(0.0, min(20.0, raw_risk))

    # Verdict
    if final_risk_score < 4.0:
        verdict = "Low Risk"
    elif final_risk_score < 8.0:
        verdict = "High Risk"
    else:
        verdict = "Critical Risk"

    return G1GroundTruthV2(
        n_mild=n_mild,
        n_moderate=n_moderate,
        n_severe=n_severe,
        n_total_incidents=n_total_incidents,
        n_positive=n_positive,
        n_negative=n_negative,
        n_betrayal=n_betrayal,
        n_allergy_reviews=n_allergy_reviews,
        trust_raw=round(trust_raw, 3),
        trust_score=round(trust_score, 3),
        mild_weight=round(mild_weight, 3),
        moderate_weight=round(moderate_weight, 3),
        severe_weight=severe_weight,
        adjusted_incident_score=round(adjusted_incident_score, 3),
        n_recent=n_recent,
        n_old=n_old,
        recent_ratio=round(recent_ratio, 3),
        trajectory_multiplier=trajectory_multiplier,
        cuisine_modifier=cuisine_modifier,
        silence_penalty=round(silence_penalty, 3),
        cuisine_impact=round(cuisine_impact, 3),
        most_recent_incident_year=most_recent_incident_year,
        incident_age=incident_age,
        recency_decay=round(recency_decay, 3),
        total_incident_weight=round(total_weight, 3),
        credibility_factor=round(credibility_factor, 3),
        incident_impact=round(incident_impact, 3),
        trust_impact=round(trust_impact, 3),
        positive_credit=round(positive_credit, 3),
        raw_risk=round(raw_risk, 3),
        final_risk_score=round(final_risk_score, 2),
        verdict=verdict
    )


def load_judgments() -> Dict[str, Dict]:
    """Load all judgments from file."""
    if not JUDGMENTS_FILE.exists():
        raise FileNotFoundError(f"Judgments file not found: {JUDGMENTS_FILE}")

    with open(JUDGMENTS_FILE, 'r') as f:
        data = json.load(f)

    return data.get("judgments", {})


def compute_gt_for_k(restaurant_name: str, k: int = None, version: str = None):
    """
    Compute GT for a restaurant using only reviews 0 to k-1.

    This enables fair evaluation when testing with different context sizes.
    A model seeing K reviews should be scored against GT from the same K reviews.

    Args:
        restaurant_name: Name of the restaurant
        k: Number of reviews to consider (0 to k-1). If None, use all reviews.
        version: Formula version ("v1" or "v2"). If None, use DEFAULT_FORMULA_VERSION.

    Returns:
        G1GroundTruth (v1) or G1GroundTruthV2 (v2) dataclass computed from filtered reviews

    Example:
        # GT from first 50 reviews only (v1 formula)
        gt = compute_gt_for_k("Vetri Cucina", k=50)

        # GT with v2 formula (harder)
        gt = compute_gt_for_k("Vetri Cucina", k=50, version="v2")
    """
    if version is None:
        version = DEFAULT_FORMULA_VERSION

    all_judgments = load_judgments()

    if restaurant_name not in all_judgments:
        raise ValueError(f"No judgments found for: {restaurant_name}")

    data = all_judgments[restaurant_name]

    # Filter reviews by original index (reviews have 'idx' field from source dataset)
    if k is not None:
        filtered_reviews = [r for r in data.get("reviews", []) if r.get("idx", 0) < k]
    else:
        filtered_reviews = data.get("reviews", [])

    filtered_data = {
        "restaurant_meta": data.get("restaurant_meta", {}),
        "reviews": filtered_reviews
    }

    # Compute GT using specified formula version
    if version == "v2":
        return compute_gt_from_data_v2(filtered_data)
    else:
        return compute_gt_from_data(filtered_data)


def compute_gt_from_judgments(restaurant_name: str, version: str = None):
    """
    Compute GT for a single restaurant by name.

    Args:
        restaurant_name: Name of the restaurant
        version: Formula version ("v1" or "v2"). If None, use DEFAULT_FORMULA_VERSION.

    Returns:
        G1GroundTruth (v1) or G1GroundTruthV2 (v2) dataclass
    """
    if version is None:
        version = DEFAULT_FORMULA_VERSION

    all_judgments = load_judgments()

    if restaurant_name not in all_judgments:
        raise ValueError(f"No judgments found for: {restaurant_name}")

    data = all_judgments[restaurant_name]
    if version == "v2":
        return compute_gt_from_data_v2(data)
    else:
        return compute_gt_from_data(data)


def compute_all_gt(k: int = None, version: str = None) -> Dict[str, any]:
    """
    Compute GT for all restaurants with stored judgments.

    Args:
        k: Number of reviews to consider per restaurant (0 to k-1).
           If None, use all reviews.
        version: Formula version ("v1" or "v2"). If None, use DEFAULT_FORMULA_VERSION.

    Returns:
        Dict mapping restaurant name to G1GroundTruth (v1) or G1GroundTruthV2 (v2)
    """
    if version is None:
        version = DEFAULT_FORMULA_VERSION

    all_judgments = load_judgments()
    result = {}

    for name in all_judgments:
        result[name] = compute_gt_for_k(name, k=k, version=version)

    return result


def save_computed_gt(k: int = None, version: str = None):
    """
    Compute GT for all restaurants and save to file.

    Args:
        k: Number of reviews to consider (0 to k-1). If None, use all reviews.
        version: Formula version ("v1" or "v2"). If None, use DEFAULT_FORMULA_VERSION.
    """
    if version is None:
        version = DEFAULT_FORMULA_VERSION

    all_gt = compute_all_gt(k=k, version=version)

    output = {
        "task_id": "G1a",
        "computed_at": __import__("datetime").datetime.now().isoformat(),
        "formula_version": version,
        "k": k if k is not None else "all",
        "restaurants": {}
    }

    # Collect verdict distribution
    verdicts = {"Low Risk": 0, "High Risk": 0, "Critical Risk": 0}

    for name, gt in all_gt.items():
        output["restaurants"][name] = asdict(gt)
        verdicts[gt.verdict] += 1

    output["summary"] = {
        "total_restaurants": len(all_gt),
        "verdict_distribution": verdicts
    }

    # Use different output file for different K values and versions
    suffix = ""
    if k is not None:
        suffix += f"_k{k}"
    if version != "v1":
        suffix += f"_{version}"

    if suffix:
        output_file = OUTPUT_FILE.parent / f"computed_gt{suffix}.json"
    else:
        output_file = OUTPUT_FILE

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    return output, output_file


def print_gt(restaurant_name: str = None, k: int = None, version: str = None):
    """Print GT for one or all restaurants."""
    if version is None:
        version = DEFAULT_FORMULA_VERSION

    if restaurant_name:
        gt = compute_gt_for_k(restaurant_name, k=k, version=version)
        k_str = f"K={k}" if k else "all reviews"
        print(f"\n{'='*60}")
        print(f"G1a Ground Truth ({version}): {restaurant_name} ({k_str})")
        print(f"{'='*60}")
        for field, value in asdict(gt).items():
            print(f"  {field}: {value}")
    else:
        all_gt = compute_all_gt(k=k, version=version)
        k_str = f"K={k}" if k else "all reviews"
        verdicts = {"Low Risk": 0, "High Risk": 0, "Critical Risk": 0}
        for name, gt in all_gt.items():
            verdicts[gt.verdict] += 1
            print(f"{name}: {gt.verdict} (score={gt.final_risk_score})")
        print(f"\nDistribution ({version}, {k_str}): {verdicts}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compute G1a Ground Truth")
    parser.add_argument("--restaurant", type=str, help="Compute for specific restaurant")
    parser.add_argument("--save", action="store_true", help="Save computed GT to file")
    parser.add_argument("--k", type=int, help="Number of reviews to use (0 to k-1)")
    parser.add_argument("--version", type=str, choices=["v1", "v2"], default=None,
                        help="Formula version (v1=simple, v2=harder with trust/trajectory)")
    parser.add_argument("--compare", action="store_true",
                        help="Compare V1 vs V2 verdict distributions")
    args = parser.parse_args()

    if args.compare:
        # Compare V1 vs V2 distributions
        print("\n" + "="*60)
        print("COMPARING V1 vs V2 FORMULA DISTRIBUTIONS")
        print("="*60)

        for version in ["v1", "v2"]:
            all_gt = compute_all_gt(k=args.k, version=version)
            verdicts = {"Low Risk": 0, "High Risk": 0, "Critical Risk": 0}
            scores = []
            for gt in all_gt.values():
                verdicts[gt.verdict] += 1
                scores.append(gt.final_risk_score)

            k_str = f"K={args.k}" if args.k else "all"
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"\n{version.upper()} ({k_str}):")
            print(f"  Distribution: {verdicts}")
            print(f"  Avg Score: {avg_score:.2f}")
            print(f"  Score Range: {min(scores):.2f} - {max(scores):.2f}")
    elif args.save:
        output, output_file = save_computed_gt(k=args.k, version=args.version)
        version = args.version or DEFAULT_FORMULA_VERSION
        k_str = f"K={args.k}" if args.k else "all reviews"
        print(f"Saved GT for {output['summary']['total_restaurants']} restaurants ({version}, {k_str})")
        print(f"Distribution: {output['summary']['verdict_distribution']}")
        print(f"Output: {output_file}")
    else:
        print_gt(args.restaurant, k=args.k, version=args.version)
