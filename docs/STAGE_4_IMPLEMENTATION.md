# Stage 4 Implementation — Description Intelligence (LLM-Primary, Guardrail-Based)

Stage 4 converts raw listing text into **structured, explainable intelligence**.
This stage is the foundation for pricing, recommendations, and buyer summaries.

This implementation prioritizes:
- high recall from LLMs
- high precision on catastrophic signals
- deterministic, explainable outputs
- safe failure modes

---

## Core Design Philosophy

**LLM is the primary extractor.**  
**Rules are guardrails, not the brain.**

LLMs handle natural language variability and paraphrasing.
Rules exist only to guarantee detection of explicit, high-severity signals.

No stage should ever rely on a single LLM call without verification.

---

## Inputs

From scraped / normalized listing JSON:
- listing_id
- title
- description
- price (optional)
- mileage (optional)
- vehicle type (car / bike)

---

## Output Contract (Stable)

Stage 4 always outputs a **schema-valid JSON object** with:
- structured signals
- confidence per signal
- evidence text for every signal
- separation of verified vs inferred information

Downstream stages must never guess.

---

## Stage 4 Pipeline (Step-by-Step)

### Step 1 — Text Preparation

Purpose: Make extraction and evidence validation reliable.

Actions:
- normalize whitespace
- preserve original casing for evidence
- sentence segmentation
- build character offsets for evidence spans

DONE WHEN:
- any extracted evidence can be mapped back to original text exactly.

---

### Step 2 — LLM Structured Extraction (Primary)

The LLM is responsible for **broad detection and structuring**.

The LLM extracts:
- mechanical issues
- cosmetic issues
- accident / damage hints
- legal / roadworthiness hints
- maintenance claims
- performance and cosmetic modifications
- seller intent and negotiation stance
- missing critical information
- follow-up questions to ask the seller

#### LLM Constraints (Non-Negotiable)
- output **strict JSON only**
- every extracted signal MUST include:
  - short label
  - evidence text (exact quote)
  - confidence score
- if uncertain, output low confidence (never fabricate)

LLM is encouraged to capture paraphrases and implicit hints.

---

### Step 3 — Evidence Verification Layer (Critical)

Every LLM-extracted signal is validated.

Verification rules:
- evidence_text must exist verbatim in title or description
- evidence span must map to original text offsets
- if evidence is missing or paraphrased → downgrade or discard

Classification:
- **Verified signal**: exact evidence found
- **Inferred signal**: indirect wording, weak phrasing
- **Rejected signal**: no evidence in text

Only Verified and Inferred signals survive.

This step eliminates hallucinations and stabilizes outputs.

---

### Step 4 — Guardrail Rules Pass (High-Severity Safety Net)

A **small, tightly scoped rule set** runs after the LLM pass.

Rules detect explicit high-severity phrases:
- write-off / salvage / WOVR / rebuilt
- defected / no rego / no RWC / unregistered
- engine blown / gearbox slipping / overheating
- tuned / stage 2 / E85 / track car / turbo swap

Rules:
- only ADD signals
- never remove LLM signals
- always mark as Verified with high confidence

Purpose:
- guarantee catastrophic signals are never missed
- ensure deterministic detection for explicit mentions

---

### Step 5 — Merge & Normalize Signals

Merge logic:
- union of LLM + rule signals
- deduplicate by type + evidence span
- prefer rule confidence for rule-detected items
- preserve Verified vs Inferred distinction

Compute summary fields:
- overall risk level
- mods risk level
- service history level
- negotiation stance

These are deterministic functions of signal lists.

---

### Step 6 — Missing Info & Question Generation

Using final signal set:
- identify missing critical information
- generate buyer follow-up questions
- rank questions by risk impact

Questions must be:
- concrete
- seller-actionable
- tied to detected signals

Example:
- “You mentioned the car was defected — has it been cleared, and do you have paperwork?”

---

### Step 7 — Output Assembly

Final output includes:
- structured signals (verified vs inferred)
- confidence and evidence per signal
- summary risk classifications
- follow-up questions
- extraction warnings (if any)

If LLM fails entirely:
- output rules-only signals
- mark extraction_warning = "LLM unavailable"

---

## Verified vs Inferred (Important)

- **Verified**
  - exact evidence found
  - high impact on scoring

- **Inferred**
  - indirect language
  - softer impact on scoring
  - shown clearly to user

Downstream stages must penalize Verified much more than Inferred.

---

## Evaluation & Quality Checks (Required)

Maintain a labeled evaluation set (~200 listings).

Track:
- recall on write-off / defect / major mechanical issues
- hallucination rate (signals without evidence)
- stability across re-runs
- question relevance

High precision on catastrophic signals is mandatory.

---

## Definition of Done (Stage 4 MVP)

Stage 4 is MVP-complete when:
- LLM captures paraphrases and vague language
- explicit high-risk terms are never missed
- every signal has evidence + confidence
- hallucinated issues are rejected
- output is fully consumable by Stage 7 without guessing

---

## Final Rule

If you must choose between:
- missing a minor cosmetic issue
- or falsely flagging a write-off

Always miss the cosmetic issue.

Trust and safety beat recall.

Structured intelligence first.  
Scoring second.  
Natural language last.