# Stage 4 Signal Enum Dictionary (v1.0)

This document defines the **canonical enum values** used by  
**Stage 4 — Description Intelligence**.

These enums are:
- stable
- versioned
- scoring-safe
- shared across all downstream stages (7, 8, 9)

❗ No runtime output may invent new enum values.
If a new case appears, this file must be updated and version-bumped.

---

## Global Enums

### verification_level
Describes how strongly a signal is supported by text evidence.

- `verified` — exact phrase present in text
- `inferred` — indirect or implied wording

---

### severity
Used across all signal types.

- `low`
- `medium`
- `high`

---

### claimed_condition
Seller-stated vehicle condition.

- `excellent`
- `good`
- `fair`
- `needs_work`
- `unknown`

---

### service_history_level

- `none`
- `partial`
- `full`
- `unknown`

---

### mods_risk_level

- `none`
- `low`
- `medium`
- `high`
- `unknown`

---

### negotiation_stance

- `open`
- `firm`
- `unknown`

---

### risk_level_overall
Derived summary (computed, not LLM-decided).

- `low`
- `medium`
- `high`
- `unknown`

---

# Signal Enums

All signal objects must include:
- `type` (enum)
- `severity`
- `verification_level`
- `evidence_text`
- `confidence`

---

## A) signals.legality[].type

Used for registration, roadworthiness, and legal compliance risk.

- `no_rego`
- `rego_expired`
- `rego_short`
- `unregistered`
- `no_rwc`
- `rwc_required`
- `defected`
- `inspection_required`
- `not_roadworthy`
- `non_compliant_mods`

---

## B) signals.accident_history[].type

Used for accidents, structural damage, or insurance history.

- `writeoff`
- `repairable_writeoff`
- `rebuilt_title`
- `salvage_title`
- `wovr_listed`
- `accident_damage`
- `hail_damage`
- `flood_damage`
- `structural_damage`
- `airbag_deployed`
- `chassis_damage`
- `paintwork_repair`
- `panel_replacement`

---

## C) signals.mechanical_issues[].type

### Engine & Cooling
- `engine_knock`
- `engine_misfire`
- `engine_overheating`
- `oil_leak`
- `coolant_leak`
- `head_gasket_suspected`
- `smoke_from_exhaust`
- `rough_idle`
- `starting_issue`

### Transmission & Drivetrain
- `gearbox_issue`
- `clutch_issue`
- `slipping_transmission`
- `diff_issue`
- `drivetrain_noise`

### Suspension / Brakes / Steering
- `suspension_issue`
- `steering_issue`
- `brake_issue`
- `tyres_worn`

### Electrical
- `battery_issue`
- `alternator_issue`
- `electrical_fault`

### General
- `check_engine_light`
- `needs_mechanic`
- `not_running`
- `intermittent_issue`
- `unknown_mechanical_issue`

---

## D) signals.cosmetic_issues[].type

- `scratch`
- `dent`
- `paint_fade`
- `clearcoat_peel`
- `rust_visible`
- `interior_wear`
- `cracked_windscreen`
- `broken_light`
- `missing_parts_cosmetic`
- `dirty_or_neglected`

---

## E) signals.mods_performance[].type

High impact on reliability, legality, and flipability.

- `tuned`
- `ecu_tune`
- `stage_1`
- `stage_2_or_higher`
- `turbo_upgrade`
- `turbo_swap`
- `supercharger`
- `engine_swap`
- `e85_flex_fuel`
- `intake_exhaust`
- `downpipe`
- `intercooler_upgrade`
- `fuel_system_upgrade`
- `track_use`
- `race_build`

---

## F) signals.mods_cosmetic[].type

- `aftermarket_wheels`
- `bodykit`
- `wrap`
- `tint`
- `lowered`
- `lifted`
- `custom_lights`
- `interior_custom`
- `audio_upgrade`

---

## G) signals.seller_behavior[].type

### Negotiation & Urgency
- `need_gone`
- `moving_sale`
- `urgent_sale`
- `price_drop_mentioned`
- `firm_price`
- `open_to_offers`
- `no_timewasters`
- `no_lowballers`

### Transaction Patterns
- `swap_trade`
- `cash_only`
- `deposit_required`
- `finance_available`
- `delivery_available`

### Disclosure & Trust Signals
- `transparent_disclosure`
- `vague_description`
- `contradictory_claims`
- `too_good_to_be_true_language`

---

# Maintenance Enums

## maintenance.claims[].type

- `serviced_recently`
- `regular_service_claimed`
- `logbook_mentioned`
- `receipts_mentioned`
- `major_service_done`
- `timing_belt_done`
- `water_pump_done`
- `clutch_replaced`
- `gearbox_rebuilt`
- `engine_rebuilt`
- `new_tyres`
- `new_brakes`
- `battery_replaced`

---

## maintenance.evidence_present[]

- `logbook`
- `receipts`
- `workshop_invoice`
- `photos_of_records`
- `none`

---

## maintenance.red_flags[].type

- `claim_without_proof`
- `major_work_no_receipts`
- `inconsistent_service_story`
- `recent_issue_disguised_as_minor`
- `odometer_or_history_unclear`

---

# Missing Information Enums

## missing_info[]

Used to drive follow-up questions and known-unknowns.

- `vin_unknown`
- `ppsr_or_finance_status_unknown`
- `rego_expiry_unknown`
- `rwc_status_unknown`
- `accident_history_unknown`
- `service_history_unknown`
- `number_of_owners_unknown`
- `reason_for_selling_unknown`
- `recent_repairs_proof_unknown`
- `mods_engineered_unknown`
- `inspection_availability_unknown`

---

# Usage Rules (IMPORTANT)

1. Do NOT invent enum values at runtime.
2. Use the closest existing enum if wording differs.
3. Use `unknown_*` enums instead of guessing.
4. Severity determines penalty — type determines category.
5. Verified signals must always outweigh inferred ones.

---

# Versioning

- stage4_signal_enums_version: **v1.0**
- Any change requires:
  - version bump
  - schema update
  - documentation update

---

**Final Principle**

If the enum cannot be defended in front of a buyer,
it should not exist.

Accuracy > Recall  
Trust > Coverage