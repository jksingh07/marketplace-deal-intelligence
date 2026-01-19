# Comparable Retrieval

How to find and rank comparable listings for pricing and alternatives.

## Purpose

Retrieve listings similar enough to the target for valid comparison.

## Criteria

### Must Match

- Vehicle type (e.g., car vs. bike)
- Make (exact or near-exact)
- Model (exact or near-exact)
- Year range (±2 years typically)
- Location (same city/region preferred)

### Should Match

- Mileage (within similar range)
- Condition (if available)
- Features/trim level (if available)

### Optional Matches

- Color
- Specific features
- Seller type

## Retrieval Strategy

1. **Broad Match:** Get all listings matching must-match criteria
2. **Rank:** Score by similarity (year, mileage, condition)
3. **Filter:** Remove outliers (e.g., very high/low prices)
4. **Limit:** Return top N comparables (typically 10-50)

## Scoring Similarity

```python
similarity_score = (
    year_similarity * 0.3 +
    mileage_similarity * 0.3 +
    condition_similarity * 0.2 +
    price_reasonableness * 0.2
)
```

## Usage

- **Stage 7:** Use comparables for market price estimation
- **Stage 8:** Use comparables to find better alternatives
- **Both:** Require minimum comps count (e.g., 5) for confidence

## Caching

- Cache comparable listings per target listing
- Invalidate when:
  - New listings added
  - Comp prices change significantly
  - Target listing attributes change
