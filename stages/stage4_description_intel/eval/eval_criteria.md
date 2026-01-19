# Evaluation Criteria for Stage 4

How to measure if Stage 4 is working correctly.

## Core Requirements

### 1. Schema Validity
- **Metric:** 100% of outputs must be valid JSON matching the schema
- **How to test:** Run on 100+ listings, validate all outputs
- **Pass criteria:** Zero invalid outputs

### 2. High-Risk Signal Detection
- **Metric:** Precision and Recall for write-off/defect signals
- **How to test:** Use labeled evaluation set
- **Pass criteria:** Precision > 0.95, Recall > 0.90

### 3. Evidence Presence
- **Metric:** % of flagged signals with valid evidence_text
- **How to test:** Check that all non-empty signal arrays have evidence
- **Pass criteria:** 100% of signals have evidence_text

### 4. Hallucination Prevention
- **Metric:** % of LLM-extracted issues not present in source text
- **How to test:** Spot-check LLM outputs against source
- **Pass criteria:** < 5% hallucination rate

### 5. Question Quality
- **Metric:** Subjective review of generated questions
- **How to test:** Manual review of sample outputs
- **Pass criteria:** Questions are actionable and relevant

## Regression Tests

Maintain a small set of test cases that must always pass:

1. Listing with "write off" → must flag write-off signal
2. Listing with "defected" → must flag defect signal
3. Listing with "tuned" → must flag performance mods
4. Listing with no issues → should not invent issues
5. Empty description → should produce schema-valid output with unknowns

## Continuous Monitoring

Track these metrics over time:
- Schema validation failure rate
- Average confidence scores
- Signal detection rates by category
- Question generation hit rate
