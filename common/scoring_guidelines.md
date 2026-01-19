# Scoring Guidelines

How to compute scores consistently across stages.

## Score Ranges

- **0-10 scale:** Used for overall scores, flipability, fit
- **0-1 scale:** Used for confidence, normalized metrics
- **Percentages:** Used for deal delta, price differences

## Overall Score (0-10)

Combination of multiple factors:

```python
overall_score = (
    price_score * 0.3 +
    condition_score * 0.3 +
    risk_score * 0.2 +
    value_score * 0.2
)
```

**Interpretation:**
- 8-10: Excellent deal
- 6-7.9: Good deal
- 4-5.9: Fair deal
- 2-3.9: Poor deal
- 0-1.9: Avoid

## Deal Rating

- **Bargain:** Asking price < 25th percentile of market
- **Fair:** Asking price between 25th-75th percentile
- **Overpriced:** Asking price > 75th percentile

## Risk Scoring

- **Low risk:** No red flags, clean history
- **Medium risk:** Some concerns, manageable
- **High risk:** Major red flags (write-off, defects, etc.)

## Confidence Scores

- **High (0.8-1.0):** Strong evidence, many comparables
- **Medium (0.5-0.7):** Some evidence, limited comparables
- **Low (<0.5):** Weak evidence, few/no comparables

## Consistency

- Same inputs → same scores (deterministic)
- Scores should be explainable
- Document score calculation methods
- Version score formulas when they change
