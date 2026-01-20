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
2. **All signals must have evidence text spans** - Prevents hallucinations
3. **High-risk signals prioritized** - Write-off, defect detected via guardrail rules first
4. **Schema-valid always** - Outputs always conform to JSON Schema contract
5. **Resilient by design** - Unknown LLM outputs map to `"other"` instead of failing
6. **Idempotent** - Same inputs produce identical outputs

## Input Handling

- `vehicle_type` defaults to "unknown" when not present in input
- Title and description are concatenated for text analysis
- Original text is preserved for evidence matching