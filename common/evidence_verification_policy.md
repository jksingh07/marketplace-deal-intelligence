# Evidence Verification Policy (Stage 4) — v1.0

This policy prevents hallucinations and stabilizes outputs across reruns.

---

## Definitions

### Evidence Text
A short exact quote taken from the listing title or description that justifies a signal.

### Verified signal
- evidence_text exists verbatim in the input text
- evidence_text includes explicit wording indicating the signal
- verification_level = verified

### Inferred signal
- evidence_text exists verbatim in input text
- wording implies risk but is indirect or vague
- verification_level = inferred

Examples of inference language:
- "needs love"
- "easy fix"
- "minor issue"
- "not sure what's wrong"
- "could be"

Inferred signals must still include exact evidence_text.

### Rejected signal
- evidence_text not found verbatim in input
- or evidence_text is paraphrased
- or signal cannot be tied to a specific phrase/sentence

Rejected signals must not appear in output.

---

## Hard Rules (Non-negotiable)

1) No signal without evidence_text.
2) evidence_text must be an exact substring of (title + description).
3) If evidence_text cannot be verified → reject the signal.
4) Verified signals override inferred signals in downstream scoring.
5) When uncertain between verified vs inferred → choose inferred, lower confidence.

---

## Confidence Guidelines

- verified + explicit: 0.90–1.00
- inferred + vague: 0.40–0.70
- inferred but strong implication: 0.70–0.85

Confidence should not be 1.0 unless the wording is unambiguous (e.g., "write-off", "defected").

---

## Severity Guidelines

Severity is separate from confidence:
- severity = impact level if true
- confidence = probability it is true

Example:
- "might be overheating" → severity HIGH, confidence MEDIUM/LOW, verification inferred.

---

## Evidence Window Recommendations

Preferred evidence_text form:
- full sentence containing the key phrase

If sentence extraction is unreliable:
- use a 120–200 character window containing the match,
  but ensure it’s still readable.

---

## Output Requirements

Every signal object must include:
- type (enum)
- severity
- verification_level
- evidence_text
- confidence

No exceptions.

---

## Versioning

- evidence_policy_version: v1.0
- Any change must be recorded in contracts/VERSION.md