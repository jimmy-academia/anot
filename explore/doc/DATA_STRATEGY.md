# Data Strategy: Stratified Slices

**Recommendation**: Do **NOT** Randomly Sample 100 contexts from the global dataset.

## The "Excellent Researcher" Approach

A random sample of 100 from 10k introduces too many **Confounding Variables** (Region, Cuisine, Cost of Living, language norms). It makes it impossible to know if a failure is due to *reasoning* or *domain mismatch*.

### 1. The Strategy: "Anchor & Generalize"
We should define the benchmark on a **Primary Slice** first, then prove robustness on a **Transfer Slice**.

*   **Primary Slice**: `Philadelphia` + `Restaurants` (Broad).
    *   *Why City?* Controls for "Price" ($35 is cheap in NY, expensive in Ohio) and "Culture" (Tipping norms).
    *   *Why Broad Category?* "Coffee" is too narrow for tasks like "Date Night" or "Wine List". "Restaurants" covers all 10 Perspectives.

### 2. Stratified Selection (The Core 100)
Select the 100 restaurants to ensure **Variance** across key difficulties. Do not just pick the "Top 100".

We need a distribution of:
1.  **Volume**: High (1k+ reviews) vs. Low (50 reviews).
    *   *Tests*: Needle-in-Haystack limits.
2.  **Sentiment**: High (4.5+) vs. Low (2.0) vs. **Controversial** (3.5 with high variance).
    *   *Tests*: Conflict resolution and bias.
3.  **Topic Density**: Contexts rich in specific signals (e.g., "Allergy mentions", "Wait time mentions").
    *   *Tests*: Specific primitives (G1, G5).

### 3. Implementation Plan
1.  **Filter**: `City = Philadephia`, `Categories contains 'Restaurants'`.
2.  **Stratify**: Bucket into 4 quadrants (High/Low Stars x High/Low Vol). Select 25 from each.
3.  **Validate**: Ensure the "Date Night" and "Allergy" tasks have at least 10 valid targets in this set.

## Justification for 5 Fixed Categories
We restrict the Core 100 to 5 distinct categories (Italian, Coffee, Pizza, Steak, Chinese) rather than random sampling.

### Scientific Rationale
1.  **Statistical Power**: By selecting **20 contexts per category**, we achieve a sample size large enough to claim significant failures within a domain (e.g., "Models notably fail at *Authenticity* reasoning in Chinese contexts"). Random sampling would result in N=1 or N=2 per category, making such insights impossible.
2.  **Reasoning Coverage**: These 5 categories cover the full spectrum of our 10 Reasoning Primitives:
    *   **Steakhouses ($$$$)**: Tests *Service* (G4) and *Premium Strategy* (G6).
    *   **Coffee/Pizza ($)**: Tests *Value* (G3), *Speed* (G5), and *Work/Study Suitability* (G7).
    *   **Chinese/Italian**: Tests *Cultural Authenticity* (G8) and *Ingredient Complexity* (G1).
3.  **Structural Variance**:
    *   *Menu Structure*: Single-item (Pizza) vs. Course-based (Italian/Steak) vs. Family-style (Chinese).
    *   *Service Model*: Counter-service (Coffee) vs. White-tablecloth (Steak).

This maximizes our ability to stress-test the "Logic" of the model across different data structures while controlling variables.

## Review Scaling Strategy
To test "Time Awareness" (G8) and "Needle-in-Haystack" retrieval, we scale N reviews using the **Newest-First** sorting.

| Scale (N) | Logic Coverage | Rationale |
| :--- | :--- | :--- |
| **N=25** | **Current State** | Focuses on "Now" (Operating Hours, Current Menu). |
| **N=50** | **Recent History** | Guarantees pre-2020 overlap. Good for "Short-term vs Long-term" trends. |
| **N=100** | **Deep History** | Strong chronological depth. |
| **N=200** | **Full Context** | Needle-in-Haystack stress test. |

## Why this is Publishable
It demonstrates **Internal Validity** (Controlled Experiment) before claiming **External Validity** (Generalization).
