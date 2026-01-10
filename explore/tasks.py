#!/usr/bin/env python3
"""
L2 Task Definitions

Each task defines:
- GroundTruth dataclass
- compute_ground_truth(reviews, restaurant) -> GroundTruth
- PROMPT: str (pure task instructions, no formatting)
- TOLERANCES: dict (field tolerances for scoring)
"""

from dataclasses import dataclass
from typing import List, Dict, Any


# =============================================================================
# TASK A: RECENT VS HISTORICAL
# =============================================================================

@dataclass
class TaskAGroundTruth:
    n_total: int
    n_recent: int
    n_historical: int
    avg_recent: float
    avg_historical: float
    delta: float
    direction: str
    recent_5star_ratio: float
    historical_5star_ratio: float
    recent_1star_ratio: float
    historical_1star_ratio: float


def compute_task_a_ground_truth(reviews: List[Any], restaurant: Any = None) -> TaskAGroundTruth:
    n = len(reviews)
    split_idx = (2 * n) // 3

    historical = reviews[:split_idx]
    recent = reviews[split_idx:]

    avg_hist = sum(r['stars'] for r in historical) / len(historical) if historical else 0
    avg_recent = sum(r['stars'] for r in recent) / len(recent) if recent else 0
    delta = round(avg_recent - avg_hist, 2)

    if delta > 0.3:
        direction = "IMPROVING"
    elif delta < -0.3:
        direction = "DECLINING"
    else:
        direction = "STABLE"

    recent_5star = sum(1 for r in recent if r['stars'] == 5) / len(recent) if recent else 0
    hist_5star = sum(1 for r in historical if r['stars'] == 5) / len(historical) if historical else 0
    recent_1star = sum(1 for r in recent if r['stars'] == 1) / len(recent) if recent else 0
    hist_1star = sum(1 for r in historical if r['stars'] == 1) / len(historical) if historical else 0

    return TaskAGroundTruth(
        n_total=n,
        n_recent=len(recent),
        n_historical=len(historical),
        avg_recent=round(avg_recent, 2),
        avg_historical=round(avg_hist, 2),
        delta=delta,
        direction=direction,
        recent_5star_ratio=round(recent_5star, 3),
        historical_5star_ratio=round(hist_5star, 3),
        recent_1star_ratio=round(recent_1star, 3),
        historical_1star_ratio=round(hist_1star, 3),
    )


TASK_A_PROMPT = """Analyze temporal patterns in the reviews.

The reviews are sorted chronologically. Split them into:
- Historical: First 2/3 of reviews (older)
- Recent: Last 1/3 of reviews (newer)

Compute:
1. N_TOTAL: Total number of reviews
2. N_RECENT: Number of recent reviews (last 1/3)
3. N_HISTORICAL: Number of historical reviews (first 2/3)
4. AVG_RECENT: Average star rating of recent reviews (2 decimal places)
5. AVG_HISTORICAL: Average star rating of historical reviews (2 decimal places)
6. DELTA: AVG_RECENT - AVG_HISTORICAL (2 decimal places)
7. DIRECTION: "IMPROVING" if DELTA > 0.3, "DECLINING" if DELTA < -0.3, else "STABLE"
8. RECENT_5STAR_RATIO: Fraction of recent reviews with 5 stars (3 decimal places)
9. HISTORICAL_5STAR_RATIO: Fraction of historical reviews with 5 stars (3 decimal places)
10. RECENT_1STAR_RATIO: Fraction of recent reviews with 1 star (3 decimal places)
11. HISTORICAL_1STAR_RATIO: Fraction of historical reviews with 1 star (3 decimal places)"""

TASK_A_TOLERANCES = {'delta': 0.1, 'avg_recent': 0.1, 'avg_historical': 0.1}


# =============================================================================
# TASK B: CREDIBILITY WEIGHTING
# =============================================================================

@dataclass
class TaskBGroundTruth:
    n_total: int
    n_high_useful: int
    n_low_useful: int
    avg_all: float
    avg_high_useful: float
    avg_low_useful: float
    credibility_weighted_avg: float
    high_vs_low_delta: float
    divergence_score: float


def compute_task_b_ground_truth(reviews: List[Any], restaurant: Any = None) -> TaskBGroundTruth:
    n = len(reviews)

    high_useful = [r for r in reviews if r['useful'] >= 3]
    low_useful = [r for r in reviews if r['useful'] == 0]

    avg_all = sum(r['stars'] for r in reviews) / n if n else 0
    avg_high = sum(r['stars'] for r in high_useful) / len(high_useful) if high_useful else 0
    avg_low = sum(r['stars'] for r in low_useful) / len(low_useful) if low_useful else 0

    total_weight = sum(r['useful'] + 1 for r in reviews)
    weighted_sum = sum(r['stars'] * (r['useful'] + 1) for r in reviews)
    weighted_avg = weighted_sum / total_weight if total_weight else 0

    mean = avg_all
    variance = sum((r['stars'] - mean) ** 2 for r in reviews) / n if n else 0

    return TaskBGroundTruth(
        n_total=n,
        n_high_useful=len(high_useful),
        n_low_useful=len(low_useful),
        avg_all=round(avg_all, 2),
        avg_high_useful=round(avg_high, 2),
        avg_low_useful=round(avg_low, 2),
        credibility_weighted_avg=round(weighted_avg, 2),
        high_vs_low_delta=round(avg_high - avg_low, 2) if high_useful and low_useful else 0.0,
        divergence_score=round(variance, 2),
    )


TASK_B_PROMPT = """Analyze review credibility patterns.

The "useful" field indicates how many other users found each review helpful.
- High useful (>= 3): More credible reviews
- Low useful (= 0): Less established reviews

Compute:
1. N_TOTAL: Total number of reviews
2. N_HIGH_USEFUL: Reviews with useful >= 3
3. N_LOW_USEFUL: Reviews with useful = 0
4. AVG_ALL: Average star rating of all reviews (2 decimal places)
5. AVG_HIGH_USEFUL: Average star rating of high-useful reviews (0 if none, 2 decimal places)
6. AVG_LOW_USEFUL: Average star rating of low-useful reviews (0 if none, 2 decimal places)
7. CREDIBILITY_WEIGHTED_AVG: Weighted average where weight = useful + 1
   Formula: sum(stars * (useful+1)) / sum(useful+1) (2 decimal places)
8. HIGH_VS_LOW_DELTA: AVG_HIGH_USEFUL - AVG_LOW_USEFUL (0 if either group empty, 2 decimal places)
9. DIVERGENCE_SCORE: Variance of star ratings = sum((stars - mean)^2) / N (2 decimal places)"""

TASK_B_TOLERANCES = {
    'avg_all': 0.1, 'avg_high_useful': 0.1, 'avg_low_useful': 0.1,
    'credibility_weighted_avg': 0.1, 'divergence_score': 0.1
}


# =============================================================================
# TASK C: RATING-TEXT ALIGNMENT
# =============================================================================

@dataclass
class TaskCGroundTruth:
    n_total: int
    n_positive_text: int
    n_negative_text: int
    n_aligned: int
    n_misaligned: int
    alignment_ratio: float
    avg_aligned_stars: float
    avg_misaligned_stars: float


def _has_positive_sentiment(text: str) -> bool:
    positive_words = ['amazing', 'excellent', 'great', 'wonderful', 'fantastic',
                     'delicious', 'perfect', 'best', 'love', 'loved', 'awesome',
                     'incredible', 'outstanding', 'superb', 'recommend']
    text_lower = text.lower()
    return any(word in text_lower for word in positive_words)


def _has_negative_sentiment(text: str) -> bool:
    negative_words = ['terrible', 'awful', 'horrible', 'worst', 'bad', 'poor',
                     'disappointing', 'disappointed', 'disgusting', 'never again',
                     'waste', 'avoid', 'mediocre', 'overpriced', 'cold']
    text_lower = text.lower()
    return any(word in text_lower for word in negative_words)


def compute_task_c_ground_truth(reviews: List[Any], restaurant: Any = None) -> TaskCGroundTruth:
    n = len(reviews)

    positive_text = []
    negative_text = []
    aligned = []
    misaligned = []

    for r in reviews:
        is_pos = _has_positive_sentiment(r['text'])
        is_neg = _has_negative_sentiment(r['text'])

        if is_pos and not is_neg:
            positive_text.append(r)
            if r['stars'] >= 4:
                aligned.append(r)
            else:
                misaligned.append(r)
        elif is_neg and not is_pos:
            negative_text.append(r)
            if r['stars'] <= 2:
                aligned.append(r)
            else:
                misaligned.append(r)

    n_classified = len(positive_text) + len(negative_text)

    return TaskCGroundTruth(
        n_total=n,
        n_positive_text=len(positive_text),
        n_negative_text=len(negative_text),
        n_aligned=len(aligned),
        n_misaligned=len(misaligned),
        alignment_ratio=round(len(aligned) / n_classified, 3) if n_classified else 0.0,
        avg_aligned_stars=round(sum(r['stars'] for r in aligned) / len(aligned), 2) if aligned else 0.0,
        avg_misaligned_stars=round(sum(r['stars'] for r in misaligned) / len(misaligned), 2) if misaligned else 0.0,
    )


TASK_C_PROMPT = """Analyze rating-text alignment in the reviews.

For each review, determine:
- Positive text: Contains positive sentiment words (amazing, excellent, great, delicious, love, recommend, etc.)
- Negative text: Contains negative sentiment words (terrible, awful, horrible, disappointing, avoid, etc.)
- Aligned: Positive text with 4-5 stars, OR negative text with 1-2 stars
- Misaligned: Positive text with 1-3 stars, OR negative text with 3-5 stars

Note: Reviews with mixed sentiment (both positive and negative words) or neutral sentiment are excluded.

Compute:
1. N_TOTAL: Total reviews
2. N_POSITIVE_TEXT: Reviews with clearly positive sentiment (no negative words)
3. N_NEGATIVE_TEXT: Reviews with clearly negative sentiment (no positive words)
4. N_ALIGNED: Reviews where sentiment matches rating
5. N_MISALIGNED: Reviews where sentiment contradicts rating
6. ALIGNMENT_RATIO: N_ALIGNED / (N_POSITIVE_TEXT + N_NEGATIVE_TEXT) (3 decimal places)
7. AVG_ALIGNED_STARS: Average rating of aligned reviews (0 if none, 2 decimal places)
8. AVG_MISALIGNED_STARS: Average rating of misaligned reviews (0 if none, 2 decimal places)"""

TASK_C_TOLERANCES = {'alignment_ratio': 0.1, 'avg_aligned_stars': 0.2, 'avg_misaligned_stars': 0.2}


# =============================================================================
# TASK D: CROSS-ASPECT CORRELATION
# =============================================================================

def _detect_aspects(text: str) -> Dict[str, str]:
    text_lower = text.lower()
    aspects = {}

    food_pos = ['delicious', 'tasty', 'fresh', 'amazing food', 'great food', 'excellent food']
    food_neg = ['bland', 'cold food', 'stale', 'undercooked', 'overcooked', 'tasteless']
    if any(w in text_lower for w in food_pos):
        aspects['food'] = 'positive'
    elif any(w in text_lower for w in food_neg):
        aspects['food'] = 'negative'

    service_pos = ['friendly', 'attentive', 'great service', 'excellent service', 'helpful']
    service_neg = ['rude', 'slow service', 'ignored', 'terrible service', 'inattentive']
    if any(w in text_lower for w in service_pos):
        aspects['service'] = 'positive'
    elif any(w in text_lower for w in service_neg):
        aspects['service'] = 'negative'

    wait_pos = ['no wait', 'seated immediately', 'quick', 'fast']
    wait_neg = ['long wait', 'waited forever', 'slow', 'took forever', 'hour wait']
    if any(w in text_lower for w in wait_pos):
        aspects['wait'] = 'positive'
    elif any(w in text_lower for w in wait_neg):
        aspects['wait'] = 'negative'

    value_pos = ['great value', 'worth it', 'reasonable price', 'good price', 'affordable']
    value_neg = ['overpriced', 'expensive', 'not worth', 'rip off', 'too pricey']
    if any(w in text_lower for w in value_pos):
        aspects['value'] = 'positive'
    elif any(w in text_lower for w in value_neg):
        aspects['value'] = 'negative'

    ambiance_pos = ['cozy', 'nice atmosphere', 'great ambiance', 'romantic', 'beautiful']
    ambiance_neg = ['loud', 'noisy', 'crowded', 'dirty', 'cramped']
    if any(w in text_lower for w in ambiance_pos):
        aspects['ambiance'] = 'positive'
    elif any(w in text_lower for w in ambiance_neg):
        aspects['ambiance'] = 'negative'

    return aspects


@dataclass
class TaskDGroundTruth:
    n_total: int
    n_multi_aspect: int
    n_food_positive: int
    n_service_positive: int
    n_wait_negative: int
    n_compensation_pattern: int
    n_systemic_negative: int
    avg_multi_aspect_stars: float
    avg_single_aspect_stars: float


def compute_task_d_ground_truth(reviews: List[Any], restaurant: Any = None) -> TaskDGroundTruth:
    n = len(reviews)

    multi_aspect = []
    single_aspect = []
    food_positive = 0
    service_positive = 0
    wait_negative = 0
    compensation = 0
    systemic_negative = 0

    for r in reviews:
        aspects = _detect_aspects(r['text'])

        if len(aspects) >= 2:
            multi_aspect.append(r)
        elif len(aspects) == 1:
            single_aspect.append(r)

        if aspects.get('food') == 'positive':
            food_positive += 1
        if aspects.get('service') == 'positive':
            service_positive += 1
        if aspects.get('wait') == 'negative':
            wait_negative += 1

        if aspects.get('wait') == 'negative' and aspects.get('food') == 'positive':
            compensation += 1

        neg_count = sum(1 for v in aspects.values() if v == 'negative')
        if neg_count >= 2:
            systemic_negative += 1

    return TaskDGroundTruth(
        n_total=n,
        n_multi_aspect=len(multi_aspect),
        n_food_positive=food_positive,
        n_service_positive=service_positive,
        n_wait_negative=wait_negative,
        n_compensation_pattern=compensation,
        n_systemic_negative=systemic_negative,
        avg_multi_aspect_stars=round(sum(r['stars'] for r in multi_aspect) / len(multi_aspect), 2) if multi_aspect else 0.0,
        avg_single_aspect_stars=round(sum(r['stars'] for r in single_aspect) / len(single_aspect), 2) if single_aspect else 0.0,
    )


TASK_D_PROMPT = """Analyze cross-aspect patterns in the reviews.

For each review, identify which aspects are mentioned and their sentiment:
- food: positive (delicious, tasty, fresh) or negative (bland, cold, stale)
- service: positive (friendly, attentive) or negative (rude, slow service, ignored)
- wait: positive (no wait, quick) or negative (long wait, slow, took forever)
- value: positive (great value, worth it) or negative (overpriced, expensive)
- ambiance: positive (cozy, nice atmosphere) or negative (loud, noisy, dirty)

Compute:
1. N_TOTAL: Total reviews
2. N_MULTI_ASPECT: Reviews mentioning 2+ different aspects with sentiment
3. N_FOOD_POSITIVE: Reviews with positive food mentions
4. N_SERVICE_POSITIVE: Reviews with positive service mentions
5. N_WAIT_NEGATIVE: Reviews with negative wait mentions
6. N_COMPENSATION_PATTERN: Reviews with BOTH negative wait AND positive food ("worth the wait")
7. N_SYSTEMIC_NEGATIVE: Reviews with 2+ negative aspects (systemic problem)
8. AVG_MULTI_ASPECT_STARS: Average rating of multi-aspect reviews (0 if none, 2 decimal places)
9. AVG_SINGLE_ASPECT_STARS: Average rating of single-aspect reviews (0 if none, 2 decimal places)"""

TASK_D_TOLERANCES = {'avg_multi_aspect_stars': 0.2, 'avg_single_aspect_stars': 0.2}


# =============================================================================
# TASK F: EXPECTATION CALIBRATION
# =============================================================================

@dataclass
class TaskFGroundTruth:
    n_total: int
    restaurant_price_tier: int
    restaurant_noise_level: str
    n_price_complaints: int
    n_noise_complaints: int
    price_complaint_ratio: float
    noise_complaint_ratio: float
    avg_stars_price_complainers: float
    price_adjusted_score: float


def compute_task_f_ground_truth(reviews: List[Any], restaurant: Any) -> TaskFGroundTruth:
    n = len(reviews)

    price_complaints = []
    noise_complaints = []

    for r in reviews:
        text_lower = r['text'].lower()

        if any(w in text_lower for w in ['expensive', 'overpriced', 'pricey', 'not worth', 'rip off']):
            price_complaints.append(r)

        if any(w in text_lower for w in ['loud', 'noisy', 'couldn\'t hear', 'too loud']):
            noise_complaints.append(r)

    price_ratio = len(price_complaints) / n if n else 0
    noise_ratio = len(noise_complaints) / n if n else 0

    attrs = restaurant.get('attributes', {})
    price_tier = attrs.get('RestaurantsPriceRange2', 2)
    noise_level = attrs.get('NoiseLevel', 'average')
    price_adjusted = 1 - (price_ratio * (5 - price_tier))

    return TaskFGroundTruth(
        n_total=n,
        restaurant_price_tier=price_tier,
        restaurant_noise_level=str(noise_level),
        n_price_complaints=len(price_complaints),
        n_noise_complaints=len(noise_complaints),
        price_complaint_ratio=round(price_ratio, 3),
        noise_complaint_ratio=round(noise_ratio, 3),
        avg_stars_price_complainers=round(sum(r['stars'] for r in price_complaints) / len(price_complaints), 2) if price_complaints else 0.0,
        price_adjusted_score=round(max(0, price_adjusted), 3),
    )


TASK_F_PROMPT = """Analyze reviews relative to restaurant expectations.

The restaurant metadata includes price tier and noise level. Evaluate how complaints relate to these attributes.

Compute:
1. N_TOTAL: Total reviews
2. RESTAURANT_PRICE_TIER: The restaurant's price tier from metadata (1-4)
3. RESTAURANT_NOISE_LEVEL: The restaurant's noise level from metadata
4. N_PRICE_COMPLAINTS: Reviews mentioning price issues (expensive, overpriced, pricey, not worth, rip off)
5. N_NOISE_COMPLAINTS: Reviews mentioning noise issues (loud, noisy, couldn't hear)
6. PRICE_COMPLAINT_RATIO: N_PRICE_COMPLAINTS / N_TOTAL (3 decimal places)
7. NOISE_COMPLAINT_RATIO: N_NOISE_COMPLAINTS / N_TOTAL (3 decimal places)
8. AVG_STARS_PRICE_COMPLAINERS: Average rating of reviews with price complaints (0 if none, 2 decimal places)
9. PRICE_ADJUSTED_SCORE: 1 - (PRICE_COMPLAINT_RATIO * (5 - PRICE_TIER)) (3 decimal places)"""

TASK_F_TOLERANCES = {'price_adjusted_score': 0.1}


# =============================================================================
# TASK REGISTRY
# =============================================================================

TASK_REGISTRY = {
    'A': {
        'name': 'Recent vs Historical',
        'ground_truth_class': TaskAGroundTruth,
        'compute_ground_truth': compute_task_a_ground_truth,
        'prompt': TASK_A_PROMPT,
        'tolerances': TASK_A_TOLERANCES,
    },
    'B': {
        'name': 'Credibility Weighting',
        'ground_truth_class': TaskBGroundTruth,
        'compute_ground_truth': compute_task_b_ground_truth,
        'prompt': TASK_B_PROMPT,
        'tolerances': TASK_B_TOLERANCES,
    },
    'C': {
        'name': 'Rating-Text Alignment',
        'ground_truth_class': TaskCGroundTruth,
        'compute_ground_truth': compute_task_c_ground_truth,
        'prompt': TASK_C_PROMPT,
        'tolerances': TASK_C_TOLERANCES,
    },
    'D': {
        'name': 'Cross-Aspect Correlation',
        'ground_truth_class': TaskDGroundTruth,
        'compute_ground_truth': compute_task_d_ground_truth,
        'prompt': TASK_D_PROMPT,
        'tolerances': TASK_D_TOLERANCES,
    },
    'F': {
        'name': 'Expectation Calibration',
        'ground_truth_class': TaskFGroundTruth,
        'compute_ground_truth': compute_task_f_ground_truth,
        'prompt': TASK_F_PROMPT,
        'tolerances': TASK_F_TOLERANCES,
    },
}


def get_task(task_id: str) -> dict:
    if task_id not in TASK_REGISTRY:
        raise ValueError(f"Unknown task: {task_id}. Available: {list(TASK_REGISTRY.keys())}")
    return TASK_REGISTRY[task_id]


def list_tasks() -> List[str]:
    return list(TASK_REGISTRY.keys())
