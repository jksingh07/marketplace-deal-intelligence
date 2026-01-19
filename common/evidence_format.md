# Evidence Format

Standard format for evidence text spans and confidence scores.

## Purpose

Every extracted signal must be traceable back to source text.

## Evidence Text

**Requirements:**
- Exact text span from source listing
- Full sentence or phrase (not single words)
- Preserve original capitalization and punctuation
- Include enough context to be meaningful

**Format:**
```json
{
  "label": "gearbox issues",
  "evidence_text": "Needs gearbox work, slipping sometimes.",
  "confidence": 0.85
}
```

## Confidence Scores

**Range:** 0.0 to 1.0

**Meaning:**
- 1.0: Explicit, unambiguous mention
- 0.8-0.9: Clear mention with some interpretation
- 0.6-0.7: Implied or indirect mention
- 0.4-0.5: Weak signal, uncertain
- < 0.4: Should generally not be included

## Rule-Based Confidence

- Exact keyword matches: 0.9-1.0
- Pattern matches: 0.7-0.9
- Fuzzy matches: 0.5-0.7

## LLM-Based Confidence

- Explicit statements: 0.8-1.0
- Inferred from context: 0.6-0.8
- Uncertain signals: < 0.6 (consider excluding)

## Using Evidence

- Display evidence text to users
- Use confidence for filtering/thresholding
- Sort signals by confidence in summaries
- Hide low-confidence signals unless explicitly requested
