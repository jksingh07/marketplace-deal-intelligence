# Stage Output Contracts & Recompute Triggers

This document defines:
- what each AI stage consumes
- what each stage produces
- when each stage should re-run

This is the **single source of truth** for pipeline dependencies.
If a stage changes, update this file.

---

## Naming Conventions

- Each stage output is stored as a separate record/table.
- Outputs are **versioned**.
- Outputs are **idempotent**.
- Outputs are always tied to a specific listing snapshot.

Common required fields for ALL stage outputs:
- listing_id
- source_snapshot_id (or scraped_at hash)
- stage_name
- stage_version
- created_at
- payload (stage-specific JSON)
- confidence (where applicable)

---

## Stage 4 — Description Intelligence

### Purpose
Extract structured, evidence-backed intelligence from listing text
using an LLM-primary pipeline with deterministic safety guardrails.

### Inputs
- Raw listing JSON
  - title
  - description
  - price (optional)
  - mileage (optional)
- Normalized listing fields (if available)

### Outputs
Each signal includes:
- type
- severity
- confidence
- evidence_text
- verification_level (verified | inferred)

Key outputs:
- claimed_condition
- mechanical_issues[]
- cosmetic_issues[]
- accident_or_writeoff_signals[]
- legality_signals (rego / RWC / defect)
- maintenance_claims[]
- service_history_level
- mods_performance[]
- mods_cosmetic[]
- mods_risk_level
- urgency_signals[]
- negotiation_stance
- swap_trade
- missing_info_questions[]
- recommended_questions_to_ask[]
- extraction_warnings[]

### Verification Semantics
- **Verified** signals:
  - exact phrase present in text
  - high confidence
  - heavy downstream penalty

- **Inferred** signals:
  - indirect or soft language
  - lower confidence
  - softer downstream impact

Downstream stages must always treat Verified signals
as higher priority than Inferred ones.

### Recompute Triggers
- new listing
- title changed
- description changed
- stage4 logic or prompt version updated
---

## Stage 7 — Price & Deal Intelligence

### Purpose
Estimate fair market value and deal quality.

### Inputs
- Normalized listing attributes
- Stage 4 output
- Comparable listings (retrieved dynamically)

### Outputs
- estimated_market_price_p25
- estimated_market_price_p50
- estimated_market_price_p75
- comps_used_count
- comps_listing_ids[]
- deal_delta
- deal_rating (bargain / fair / overpriced)
- explanation[]
- confidence

### Recompute Triggers
- Stage 4 updated
- asking price changed
- mileage changed
- year changed
- comp pool changed significantly (batch recompute)

---

## Stage 8 — Alternative Recommender

### Purpose
Find better or similar options to avoid buyer regret.

### Inputs
- Normalized listing attributes
- Stage 7 output
- Comparable listing pool

### Outputs
- better_alternatives_found (bool)
- alternatives[]
  - listing_id
  - price
  - year
  - mileage
  - value_score
  - why_better[]

### Recompute Triggers
- Stage 7 updated
- new comparable listings added
- significant price changes in comp pool

---

## Stage 9 — Buyer-Ready Summary

### Purpose
Produce user-facing guidance and recommendations.

### Inputs
- Normalized listing
- Stage 4 output
- Stage 7 output
- Stage 8 output
- (later) Stage 6 seller trust

### Outputs
- overall_score
- flipability_score
- fit_score (if user profile exists)
- verdict
- key_pros[]
- key_cons[]
- follow_up_questions[]
- negotiation_tips[]
- recommended_actions[]
- known_unknowns[]
- confidence

### Recompute Triggers
- Stage 4 updated
- Stage 7 updated
- Stage 8 updated
- seller trust updated (later)

---

## Stage 6 — Seller Profile Intelligence (Post-MVP)

### Purpose
Assess seller trust and behavioral risk.

### Inputs
- Seller profile snapshot
- Seller ratings / history
- Listing associations

### Outputs
- seller_trust_score
- rating
- rating_count
- rating_distribution
- account_age
- active_listings_count
- risk_signals[]

### Recompute Triggers
- new seller snapshot
- rating change
- listing count change

---

## Stage 5 — Image Analysis (Last Stage)

### Purpose
Extract visual risk and quality signals from images.

### Inputs
- Listing image URLs
- Stored image files

### Outputs
- image_quality_score
- photo_coverage (interior / exterior / engine / odometer)
- visual_risk_flags (low / medium / high)
- contradictions_with_description[]
- missing_photo_questions[]

### Recompute Triggers
- new images added
- image model version updated

---

## Cross-Stage Rules (Important)

1. No stage mutates another stage’s output.
2. Stages only depend on:
   - raw snapshot
   - explicitly listed upstream stages
3. All recomputation is safe and idempotent.
4. Buyer-facing text must always be traceable to structured facts.

---

## Final Rule (Read This Twice)

If you’re unsure whether logic belongs in:
- a prompt → it probably doesn’t
- Stage 9 → it probably belongs earlier
- Stage 4 → that’s usually correct

Structured intelligence first.  
Natural language last.