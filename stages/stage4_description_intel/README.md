# Stage 4: Description Intelligence

Stage 4 converts listing text into structured intelligence.

See `/docs/STAGE_4_IMPLEMENTATION.md` for detailed implementation guidance.

## Purpose

Extract structured signals from listing descriptions:
- Condition & Issues
- Maintenance Evidence
- Modifications
- Seller Intent / Negotiation Signals
- Buyer Follow-up Questions

## Key Principles

1. **LLM is the primary extractor** - Rules are guardrails, not the brain
2. All signals must have evidence text spans
3. High-risk signals (write-off, defect) are prioritized via guardrail rules
4. Output must be schema-valid always
5. Evidence verification prevents hallucinations

## Input Handling

- `vehicle_type` defaults to "unknown" when not present in input
- Title and description are concatenated for text analysis
- Original text is preserved for evidence matching