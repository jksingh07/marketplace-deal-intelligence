# Idempotency

How to ensure stage outputs are idempotent and replayable.

## Definition

Running a stage with the same inputs multiple times should produce the same output (or a deterministic update).

## Implementation

### Deterministic Inputs

- Use listing snapshot ID/hash as input identifier
- Include all required fields explicitly
- Normalize inputs before processing

### Deterministic Processing

- Fixed random seeds for any randomness
- Deterministic ordering for list operations
- No reliance on current time/date for core logic
- Cache LLM responses with same inputs

### Output Versioning

- Include `stage_version` in all outputs
- Version changes when logic changes
- Maintain backward compatibility when possible

## Idempotency Checks

Before running a stage:
1. Check if output already exists for this snapshot + stage_version
2. If exists and valid, skip processing
3. If snapshot changed, recompute

## Replay Safety

- Old outputs remain valid after stage updates
- New version produces new outputs
- Both versions can coexist
- Downstream stages use specified version
