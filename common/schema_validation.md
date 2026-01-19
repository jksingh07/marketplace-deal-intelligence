# Schema Validation

How to validate stage outputs against their contracts.

## Purpose

Ensure all stage outputs conform to their schema definitions, preventing downstream failures.

## Implementation

1. Load schema from `/contracts/{stage}_schema.json`
2. Validate output JSON against schema
3. Fail fast on validation errors
4. Log validation failures for debugging

## Validation Rules

- All required fields must be present
- Types must match (string, number, array, object)
- Enums must use valid values
- Numeric ranges must be respected
- Arrays must contain items of correct type

## Error Handling

**On validation failure:**
- Stage should not save invalid output
- Log detailed error with field paths
- Optionally fall back to minimal valid output
- Alert on repeated failures

## Testing

Run validation on:
- All stage outputs before saving
- Historical outputs during schema migrations
- Example outputs in test suites
