# Stage 4 Guardrail Rules (v1.0)

These rules are a **thin deterministic safety net**.
They are NOT the main extractor (LLM is primary).
Their only job is to guarantee that **explicit high-severity signals** are never missed.

Rules:
- only ADD signals (never remove)
- always produce `verification_level=verified`
- always include `evidence_text` as an exact substring quote
- always set high confidence (0.90–1.00) when matched

If a phrase matches multiple rules, choose the most severe / most specific type.

---

## Output Mapping (What rules produce)

Every match produces a signal object:
- type: enum from STAGE_4_SIGNAL_ENUMS.md
- severity: low/medium/high
- verification_level: verified
- evidence_text: exact matched phrase or containing sentence
- confidence: 0.90–1.00

---

## A) Accident / Write-off / Title History (HIGH)

### Map to: signals.accident_history[].type

**writeoff / salvage / title flags**
- Phrases:
  - "write off", "write-off", "written off", "written-off"
  - "repairable write off", "repairable write-off"
  - "salvage", "salvage title", "salvage vehicle"
  - "rebuilt title", "rebuilt"
  - "WOVR"
- Mapping:
  - "repairable write off" → `repairable_writeoff` (HIGH)
  - "write off" / "written off" → `writeoff` (HIGH)
  - "salvage title" → `salvage_title` (HIGH)
  - "rebuilt title" → `rebuilt_title` (HIGH)
  - "WOVR" → `wovr_listed` (HIGH)

**flood / structural**
- Phrases:
  - "flood", "flood damaged", "water damage"
  - "structural damage", "frame damage", "chassis damage"
  - "airbags deployed", "airbag deployed"
- Mapping:
  - flood → `flood_damage` (HIGH)
  - structural/frame/chassis → `structural_damage` or `chassis_damage` (HIGH)
  - airbag deployed → `airbag_deployed` (HIGH)

---

## B) Legality / Registration / Roadworthiness (HIGH)

### Map to: signals.legality[].type

**defect / unregistered**
- Phrases:
  - "defect", "defected"
  - "unregistered", "unreg", "no rego"
  - "rego expired"
- Mapping:
  - defect/defected → `defected` (HIGH)
  - unregistered/unreg/no rego → `unregistered` or `no_rego` (HIGH)
  - rego expired → `rego_expired` (HIGH)

**RWC / roadworthy**
- Phrases:
  - "no rwc", "without rwc"
  - "needs rwc", "rwc required"
  - "not roadworthy"
- Mapping:
  - no rwc → `no_rwc` (HIGH)
  - rwc required/needs rwc → `rwc_required` (MEDIUM→HIGH depending on local market defaults)
  - not roadworthy → `not_roadworthy` (HIGH)

**inspection**
- Phrases:
  - "inspection required", "blue slip", "pink slip"
- Mapping:
  - inspection required / blue slip / pink slip → `inspection_required` (MEDIUM)

---

## C) Mechanical Catastrophes (HIGH)

### Map to: signals.mechanical_issues[].type

**not running / blown**
- Phrases:
  - "not running", "won't start", "doesn't start"
  - "engine blown", "blown engine"
- Mapping:
  - not running / won't start → `not_running` (HIGH) or `starting_issue` (HIGH)
  - engine blown → `not_running` (HIGH) + (optional inferred) engine issue

**engine / gearbox red flags**
- Phrases:
  - "engine knock", "knocking"
  - "overheating", "over heats", "runs hot"
  - "gearbox issue", "gearbox problem"
  - "slipping", "slips"
- Mapping:
  - engine knock/knocking → `engine_knock` (HIGH)
  - overheating → `engine_overheating` (HIGH)
  - gearbox issue → `gearbox_issue` (HIGH)
  - slipping (if near transmission context) → `slipping_transmission` (HIGH)

**head gasket**
- Phrases:
  - "head gasket"
- Mapping:
  - head gasket → `head_gasket_suspected` (HIGH)

---

## D) High-Risk Performance Modifications (MEDIUM→HIGH)

### Map to: signals.mods_performance[].type

- Phrases:
  - "tuned", "tune", "ecu", "ecu tune"
  - "stage 2", "stage2", "stage 3", "stage3"
  - "E85", "flex fuel"
  - "track car", "track use", "race build"
  - "turbo swap", "turbo upgrade", "supercharger"
  - "engine swap"
- Mapping:
  - tuned/tune → `tuned` or `ecu_tune` (MEDIUM)
  - stage 2+ → `stage_2_or_higher` (HIGH)
  - E85/flex → `e85_flex_fuel` (HIGH)
  - track/race → `track_use` or `race_build` (HIGH)
  - turbo swap/upgrade → `turbo_swap` / `turbo_upgrade` (HIGH)
  - supercharger → `supercharger` (HIGH)
  - engine swap → `engine_swap` (HIGH)

---

## E) Negotiation Hard Flags (MEDIUM)

### Map to: signals.seller_behavior[].type

- Phrases:
  - "firm", "firm price", "price is firm", "fixed price"
  - "no lowballers", "no low ballers"
  - "no timewasters", "no time wasters"
  - "need gone", "must sell", "urgent sale"
- Mapping:
  - firm → `firm_price` (MEDIUM)
  - no lowballers → `no_lowballers` (LOW→MEDIUM)
  - no timewasters → `no_timewasters` (LOW)
  - urgent/need gone → `urgent_sale` or `need_gone` (MEDIUM)

---

## Implementation Notes (for developers)

1) Match case-insensitively.
2) Prefer exact substring match; if regex used, keep it tight.
3) evidence_text should be the containing sentence (or 120–200 chars window) including the match.
4) If multiple matches occur, create multiple signals (dedupe later by (type, evidence_text)).
5) Rules should remain small. If this file grows too large, we are doing it wrong.

---

## Versioning

- ruleset_version: v1.0
- Any mapping changes require bumping ruleset_version and updating contracts/VERSION.md