# Stage 4 Output Examples

Example outputs showing what Stage 4 produces.

## Example 1: High-Risk Listing

**Input Listing:**
```
Title: 2015 Honda Civic - Needs Work
Description: Has been in an accident, written off but repaired. 
Needs gearbox work, runs hot sometimes. Unregistered, no RWC.
```

**Stage 4 Output:**
```json
{
  "listing_id": "example_1",
  "stage_version": "1.0.0",
  "claimed_condition": "needs_work",
  "accident_or_writeoff_signals": [
    {
      "signal": "write-off",
      "evidence_text": "Has been in an accident, written off but repaired.",
      "confidence": 1.0
    }
  ],
  "legality_signals": {
    "rego": null,
    "rwc": "none",
    "defect": null,
    "unregistered": "unregistered"
  },
  "issues_mechanical": [
    {
      "label": "gearbox needs work",
      "evidence_text": "Needs gearbox work",
      "confidence": 0.9
    },
    {
      "label": "overheating",
      "evidence_text": "runs hot sometimes",
      "confidence": 0.8
    }
  ],
  "issues_cosmetic": [],
  "mods_risk_level": "low",
  "recommended_questions_to_ask": [
    "Can you provide details on the accident and repair work done?",
    "What specific gearbox issues are present?",
    "Has the overheating issue been diagnosed?"
  ]
}
```

## Example 2: Clean Listing

**Input Listing:**
```
Title: 2018 Toyota Camry - Excellent Condition
Description: One owner, full service history with logbook. 
No accidents, never modified. Selling due to upgrade.
```

**Stage 4 Output:**
```json
{
  "listing_id": "example_2",
  "stage_version": "1.0.0",
  "claimed_condition": "excellent",
  "service_history_level": "full",
  "evidence_present": "logbook",
  "accident_or_writeoff_signals": [],
  "mods_risk_level": "low",
  "urgency_signals": [],
  "negotiation_stance": "unknown",
  "recommended_questions_to_ask": [
    "Can you show the service logbook?",
    "Why are you selling?"
  ]
}
```
