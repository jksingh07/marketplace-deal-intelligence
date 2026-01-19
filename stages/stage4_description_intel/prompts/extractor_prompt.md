# Stage 4 — Description Intelligence (Extractor Prompt v1.0)

## Purpose
Extract structured intelligence from a Marketplace vehicle/bike listing’s **title + description**.

This prompt MUST output:
- strict JSON only
- schema-compliant fields
- enum-compliant signal types
- evidence_text that is an **exact quote** from title/description
- verification_level = verified/inferred
- confidence in [0, 1]

The model must not invent facts.

---

## Inputs Provided to the Model

You will receive:
- listing_id (string)
- title (string)
- description (string)
- vehicle_type (string: "car" or "bike" or "unknown")
- price (optional)
- mileage (optional)

---

## Output Requirements (NON-NEGOTIABLE)

1) Output **JSON only**. No markdown, no commentary.
2) Output must match the Stage 4 schema structure exactly:
   - top-level keys:
     - listing_id
     - source_snapshot_id
     - created_at
     - stage_name
     - stage_version
     - ruleset_version
     - llm_version
     - payload
3) Every extracted signal MUST include:
   - type (must be one of the enums in STAGE_4_SIGNAL_ENUMS.md)
   - severity (low/medium/high)
   - verification_level (verified/inferred)
   - evidence_text (EXACT QUOTE from title/description)
   - confidence (0.0–1.0)
4) If you cannot quote exact evidence, do not output the signal.
   - If the intent is implied but not explicit, you may output it as `inferred`
     ONLY if you can still quote the wording that caused the inference.
5) Never guess missing information.
6) Prefer under-extraction over hallucination.

---

## Severity Guidance (Use consistently)

HIGH severity examples:
- writeoff / repairable writeoff / defected / unregistered / not_running
- structural_damage / flood_damage / airbag_deployed
- engine_knock / gearbox_issue / engine_overheating

MEDIUM severity examples:
- oil_leak / tyres_worn / check_engine_light
- tuned / ecu_tune / stage_2_or_higher
- service history missing

LOW severity examples:
- scratch / dent / interior_wear / tint / aftermarket_wheels

---

## Verification Guidance

- verified:
  - explicit claim (“defected”, “write-off”, “tuned”, “no rego”, etc.)
- inferred:
  - indirect wording but still evidence-backed (“needs love”, “easy fix”, “minor issue”)
  - must still include the exact quoted text that implies it

---

## Output JSON Template (Fill all keys)

Use this structure and return ONLY JSON:

{
  "listing_id": "<listing_id>",
  "source_snapshot_id": "<source_snapshot_id>",
  "created_at": "<ISO-8601 datetime UTC>",
  "stage_name": "stage4_description_intelligence",
  "stage_version": "v1.0.0",
  "ruleset_version": "<ruleset_version>",
  "llm_version": "<llm_version>",
  "payload": {
    "risk_level_overall": "unknown",
    "negotiation_stance": "unknown",
    "claimed_condition": "unknown",
    "service_history_level": "unknown",
    "mods_risk_level": "unknown",
    "signals": {
      "legality": [],
      "accident_history": [],
      "mechanical_issues": [],
      "cosmetic_issues": [],
      "mods_performance": [],
      "mods_cosmetic": [],
      "seller_behavior": []
    },
    "maintenance": {
      "claims": [],
      "evidence_present": [],
      "red_flags": []
    },
    "missing_info": [],
    "follow_up_questions": [],
    "extraction_warnings": [],
    "source_text_stats": {
      "title_length": 0,
      "description_length": 0,
      "contains_keywords_high_risk": false
    }
  }
}

---

## Classification Rules (How to fill summary fields)

### claimed_condition
- excellent: “immaculate”, “like new”, “perfect”
- good: “good condition”, “well maintained”
- fair: “average”, “some wear”, “minor issues”
- needs_work: “needs work”, “project”, “mechanic special”, “not running”
- unknown: if none stated

### service_history_level
- full: explicit “full service history”, “logbooks + receipts”
- partial: “some receipts”, “serviced regularly” without proof
- none: explicit “no service history”, “no logbooks”
- unknown: not mentioned

### mods_risk_level
- none: no mods mentioned
- low: cosmetic mods only (wheels, tint)
- medium: intake/exhaust, mild tune mention, suspension
- high: stage 2+, turbo swap, E85, track/race build, engine swap
- unknown: unclear

### negotiation_stance
- firm: “firm price”, “no lowballers”, “price is fixed”
- open: “open to offers”, “negotiable”
- unknown: not mentioned

### risk_level_overall (derived)
- high: any HIGH severity verified signal exists
- medium: multiple medium signals or any medium verified + missing evidence
- low: only low cosmetic signals and no major red flags
- unknown: description too short or insufficient info

---

## Missing Info (Populate these when not mentioned)

Use the `missing_info[]` enums. Add those that are relevant and absent.

Examples:
- service history not mentioned → service_history_unknown
- rego expiry not mentioned → rego_expiry_unknown
- RWC not mentioned → rwc_status_unknown
- accident history not mentioned → accident_history_unknown

---

## Follow-up Questions (Must be concrete)

For each major risk or missing item, generate questions:

Each question object:
- question: short and direct
- reason: one line
- priority: high/medium/low
- driven_by: list of strings referencing signal types or missing_info enums

Guidelines:
- If a write-off or defect is detected → priority must include high
- If service history is missing → ask for proof
- If mods are high-risk → ask for engineering/legal compliance and receipts

---

## Common Extraction Warnings

Add warnings when:
- description is very short (< 30 chars)
- mostly emojis or unrelated content
- text seems not in English
- title/description contradict each other

---

## Important Safety Rule

If you must choose between:
- extracting more signals with uncertainty
- or staying conservative and only extracting evidence-backed signals

Always be conservative.

Return only what is supported by evidence text.