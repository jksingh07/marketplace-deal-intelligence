# Stage 4 Evaluation Set Spec (v1.0)

Goal: Evaluate Stage 4 quality with a small labeled set (200 listings) before scaling.

---

## Location in Repo

Store evaluation artifacts here:

- `stages/stage4_description_intel/eval/`
  - `labeled_listings.csv`
  - `labeling_guidelines.md`
  - `eval_criteria.md`
  - `notes.md`

Raw inputs for those listings should be saved under:
- `data_samples/raw_listing_examples/`

---

## Dataset Size

- MVP: 200 listings
- Composition goal:
  - 40 high-risk (write-off/defect/not running/tuned track builds)
  - 80 medium-risk (oil leaks, tyres worn, check engine, partial history)
  - 80 low-risk (mostly clean descriptions, minor cosmetic)

---

## CSV Columns (Required)

### Identity
- listing_id
- source_snapshot_id

### Text
- title
- description

### Labels (Binary or Enum)
Accident/Title:
- label_accident_history: none / hinted / explicit
- label_writeoff: 0/1
- label_rebuilt_or_salvage: 0/1

Legality:
- label_defected: 0/1
- label_unregistered_or_no_rego: 0/1
- label_no_rwc: 0/1

Mechanical (binary flags):
- label_engine_overheating: 0/1
- label_engine_knock: 0/1
- label_gearbox_issue: 0/1
- label_not_running: 0/1

Mods:
- label_tuned: 0/1
- label_stage2plus: 0/1
- label_e85: 0/1
- label_track_or_race: 0/1

Maintenance:
- label_service_history_level: none / partial / full / unknown

Negotiation:
- label_firm_price: 0/1
- label_need_gone_or_urgent: 0/1

Optional (quality labels):
- label_question_quality: 1–5 (human rating)
- label_hallucination_present: 0/1 (did model invent something)

---

## Metrics to Track

Critical metrics (must be strong):
- Recall on explicit write-off/defect/not running/tuned stage2+
- Precision on the same (avoid false catastrophic flags)
- Evidence correctness rate (evidence_text truly matches)

Secondary metrics:
- coverage rate (how often we extract useful signals)
- question relevance score (human 1–5)

---

## Acceptance Targets (MVP)

- Catastrophic signals (writeoff/defect/not running):
  - Precision ≥ 0.95
  - Recall ≥ 0.90
- Evidence correctness ≥ 0.98
- Hallucination rate ≤ 2%

---

## Versioning

- eval_set_version: v1.0
- If you update labels or criteria, bump the version and log it.