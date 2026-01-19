# High-Risk Terms Detection Rules

These terms trigger high-confidence risk signals and must be caught by rule-based detectors.

## Write-Off / Salvage / Rebuilt

**Keywords:**
- "write off", "writeoff", "written off"
- "salvage", "salvage title"
- "rebuilt", "rebuilt title"
- "accident", "crash", "collision"
- "repairable write-off", "RWO"

**Confidence:** 0.9-1.0 (high for exact matches)

## Defect / Unregistered / Rego Issues

**Keywords:**
- "defected", "defect notice", "defect sticker"
- "no rego", "unregistered", "rego expired"
- "no RWC", "without RWC", "needs RWC"
- "can't be registered"

**Confidence:** 0.9-1.0 (high for exact matches)

## High-Risk Mechanical Issues

**Keywords:**
- "gearbox issues", "transmission problem", "needs gearbox"
- "overheating", "runs hot"
- "engine knock", "knocking"
- "slipping clutch", "clutch needs work"
- "misfire", "missing"

**Confidence:** 0.7-0.9 (medium-high)

## High-Risk Performance Modifications

**Keywords:**
- "tuned", "ECU tuned", "remapped"
- "stage 2", "stage 3"
- "E85", "flex fuel"
- "track car", "track use"
- "turbo swap", "turbocharged", "turbo conversion"

**Confidence:** 0.7-0.9 (medium-high, context-dependent)

## Implementation Notes

- Case-insensitive matching
- Match full phrases when possible
- Extract evidence sentence containing the keyword
- Prefer rule evidence over LLM when both detect the same signal
