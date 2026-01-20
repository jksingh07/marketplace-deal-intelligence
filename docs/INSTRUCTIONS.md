# Cursor Handoff Plan — Stage 4 → MVP Pipeline

This plan defines exactly what Cursor should implement first and how to validate it.

Goal: ship Stage 4 end-to-end with notebook testing, schema validation, and outputs stored in the DB/object storage.

---

## Prerequisites (Already provided)
- docs/AI_PIPELINE_OVERVIEW.md
- docs/STAGE_OUTPUT_CONTRACTS.md
- docs/STAGE_4_SIGNAL_ENUMS.md
- contracts/stage4_description_intel.schema.json
- contracts/VERSION.md
- contracts/README.md
- stages/stage4_description_intel/prompts/extractor_prompt.md
- stages/stage4_description_intel/rules/guardrails.md
- common/evidence_verification_policy.md

---

## Implementation Sequence (Do in this order)

### Step 1 — Build Stage 4 “Runner” (local)
- Load one raw listing JSON record
- Extract title + description + listing_id
- Call LLM extractor prompt
- Parse JSON output
- Validate output against `contracts/stage4_description_intel.schema.json`

Acceptance:
- returns schema-valid JSON for at least 20 sample listings

---

### Step 2 — Evidence Verification Layer
- Verify every signal’s evidence_text is a verbatim substring
- Reject signals without evidence
- Preserve verified vs inferred from output (and enforce policy)

Acceptance:
- evidence correctness rate ≈ 100% on spot checks
- no hallucinated signals survive

---

### Step 3 — Guardrail Rules Pass
- Run guardrails from `guardrails.md` on the same text
- Add rule-detected signals as verified with high confidence
- Deduplicate with LLM signals

Acceptance:
- explicit “write-off/defected/not running” cases always flagged even if LLM misses

---

### Step 4 — Derived Summary Fields
Compute deterministically:
- risk_level_overall
- mods_risk_level
- service_history_level
- negotiation_stance
based on extracted signals + maintenance evidence.

Acceptance:
- stable output across reruns

---

### Step 5 — Storage Integration
- Store Stage 4 output to DB table/collection:
  - key: (listing_id, source_snapshot_id, stage_version)
- Never overwrite a different snapshot.

Acceptance:
- reruns do not create duplicates
- reruns update only same (listing_id, snapshot_id, stage_version) record if needed

---

### Step 6 — Notebook POC
Create a notebook that:
- loads 5–10 sample listings
- runs stage 4 step-by-step
- prints signals with evidence
- validates schema each time

Acceptance:
- rapid iteration possible without running full pipeline

---

## Folder/File Checklist (Cursor must preserve)
- contracts/
- docs/
- stages/stage4_description_intel/
- common/

---

## Testing Flow
Minimum tests:
1) schema validation test (valid output)
2) evidence verification test (reject missing evidence)
3) guardrail test cases (explicit write-off / defect / not running)
4) idempotency test (same input → stable output)

---

## Done Criteria Before Moving to Stage 7
Stage 4 is complete when:
- outputs are schema-valid and stable
- catastrophic explicit signals are never missed
- hallucination rate ~0 in practice (evidence-gated)
- follow-up questions are meaningful

Only then begin Stage 7 pricing.