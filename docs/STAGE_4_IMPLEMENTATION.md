# Stage 4 Implementation — Description Intelligence (MVP)

Stage 4 is the foundation. It converts listing text into structured intelligence.
Everything downstream (pricing, alternatives, summary) depends on this output.

This doc defines EXACT implementation steps and “done” criteria.

---

## Inputs (Minimum Required)

From scraped/normalized listing JSON:
- listing_id
- title
- description (raw text)
- price (if available)
- location (optional)
- vehicle meta if available (make/model/year/mileage)

---

## Output Contract (Must Be Stable)

Stage 4 output MUST include these sections:

A) Condition & Issues
- claimed_condition: (excellent/good/fair/needs_work/unknown)
- issues_mechanical: []
- issues_cosmetic: []
- accident_or_writeoff_signals: []
- legality_signals: (rego/rwc/defect/unregistered)

B) Maintenance Evidence
- service_history_level: (none/partial/full/unknown)
- maintenance_claims: []
- evidence_present: (logbook/receipts/workshop/none)

C) Modifications
- mods_performance: []
- mods_cosmetic: []
- mods_risk_level: (low/medium/high)

D) Seller Intent / Negotiation
- urgency_signals: []
- negotiation_stance: (open/firm/unknown)
- swap_trade: (true/false)

E) Buyer Follow-up
- missing_info_questions: []
- recommended_questions_to_ask: []  (must be concrete + actionable)

F) Evidence + Confidence (Non-negotiable)
For every high-signal item store:
- evidence_text (exact phrase/sentence)
- confidence (0–1)

---

## MVP Implementation Steps

### Step 1 — Text Normalization
Goal: make extraction reliable.
- normalize whitespace
- lowercasing for rule matching (keep original text for evidence spans)
- sentence split (even rough is OK)

DONE WHEN:
- you can extract evidence spans consistently without breaking punctuation.

---

### Step 2 — Rule Detectors (Rules First)
Goal: catch high-severity signals with high precision, even if LLM fails.

Implement detectors for:
1) Write-off / Salvage / Rebuilt / Accident
2) Defect / Unregistered / No rego / No RWC
3) Mechanical red flags (gearbox, overheating, engine knock, slipping, misfire)
4) High-risk performance mods (tuned, stage 2, E85, track car, turbo swap)

Each detector MUST output:
- label
- matched keyword/pattern
- evidence_text (sentence)
- confidence (default high for exact matches)

DONE WHEN:
- given a listing containing “write off” or “defected”, stage 4 flags it reliably.

---

### Step 3 — LLM Structured Extraction (JSON only)
Goal: extract lists + categorize issues + generate missing-info questions.

LLM responsibilities:
- extract issues_mechanical and issues_cosmetic (as short bullet phrases)
- extract maintenance claims and service evidence
- extract mods and estimate mods_risk_level
- infer negotiation stance + urgency signals
- generate missing_info_questions and recommended_questions_to_ask

LLM constraints:
- strict JSON matching schema
- no invented claims
- everything must be grounded in the given text

Validation behavior:
- If JSON invalid OR missing required keys → discard LLM output
- Fall back to rules-only output (still valid schema with empty lists where needed)

DONE WHEN:
- you can run stage 4 on 100 listings and always get schema-valid JSON.

---

### Step 4 — Merge Strategy (Rules + LLM)
Rules should always “win” on high-risk signals:
- If rules say write-off signal present, LLM cannot remove it.
- If LLM finds extra low-risk cosmetic issues, keep them.

Merge policy:
- union lists
- dedupe items
- preserve evidence spans (prefer rule evidence for rule hits)

DONE WHEN:
- rule hits always appear in final output even if LLM misses them.

---

### Step 5 — Evaluation Set (Must Have)
Create a small labeled set (~150–250 listings).

Label only the most important things:
- write-off/accident signals
- defect/rego/rwc signals
- high-risk mods
- major mechanical issues

Metrics to track:
- precision/recall on those 4 categories
- “hallucination rate” (LLM inventing issues not in text)
- question quality (spot-check)

DONE WHEN:
- precision is high on write-off/defect signals (these must be reliable).

---

## Definition of Done (Stage 4 MVP)

Stage 4 is MVP-complete when:
- Every listing produces a schema-valid output.
- High-risk terms (write-off/defect/tuned) are reliably detected.
- Output contains evidence spans for flagged risks.
- Output contains a useful list of follow-up questions.
- Stage 7 can consume stage 4 without guessing.

---

## What Stage 4 Unlocks

Once Stage 4 exists:
- Stage 7 can adjust fair price estimation using risk flags.
- Stage 8 can rank alternatives using risk level + maintenance evidence.
- Stage 9 can generate buyer-ready summaries from structured facts.