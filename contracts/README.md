# Contracts Directory

This directory contains JSON schemas that define the stable contracts between pipeline stages.

These contracts exist to prevent:
- prompt drift breaking downstream logic
- silent schema changes causing inconsistent scoring
- difficult-to-debug production failures

If you change an output format, you must update the schema and VERSION.md.

---

## How Contracts Are Used

Each stage produces an output record that:
- is tied to a specific listing snapshot (`source_snapshot_id`)
- is versioned (`stage_version`, `ruleset_version`, `llm_version`)
- validates against a JSON schema in this directory

Downstream stages must only read:
- raw snapshot
- validated upstream stage outputs

Downstream stages must never parse raw HTML directly.

---

## Versioning Strategy

We use semantic versioning (SemVer):
- MAJOR — breaking change
- MINOR — non-breaking additions
- PATCH — internal / docs / examples

### Breaking changes (MAJOR bump)
- renaming/removing fields
- changing types
- renaming enum values
- making previously optional fields required

### Non-breaking changes (MINOR bump)
- adding optional fields
- adding new enum values
- adding new stage outputs without touching existing ones

---

## Idempotency (Important)

Stage outputs are designed to be idempotent:
- given the same input snapshot and the same stage version,
  output should be stable (or minimally variant only in text phrasing, never structure).

Recommended uniqueness key for a stage output record:
- (listing_id, source_snapshot_id, stage_name, stage_version)

This prevents duplicates and supports safe retries.

---

## Evidence Policy (Stage 4)

Any extracted signal that affects scoring must contain:
- evidence_text (exact quote from listing text)
- confidence score
- verification_level (verified/inferred)

If evidence does not exist in the text:
- the signal must be rejected or downgraded to inferred with low confidence.

---

## Adding New Schemas

When adding a new schema:
1. Create the JSON schema file in this directory
2. Add it to `VERSION.md` with version number
3. Add a small example output in `data_samples/stage_outputs_examples/`
4. Ensure validation passes for the example

---

## File List

- `stage4_description_intel.schema.json` — Stage 4 output contract
- `VERSION.md` — authoritative version log