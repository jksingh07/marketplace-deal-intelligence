# Contracts Version Log

This file tracks versions for all schema contracts and enum dictionaries used across pipeline stages.

## Rules (Read Before Changing Anything)

### What counts as a BREAKING change (requires new major version)
- Renaming an existing field
- Removing a field
- Changing a field type (string → number, etc.)
- Tightening validation so previously valid outputs become invalid
- Renaming enum values
- Moving fields to different paths

### What counts as a NON-BREAKING change (minor/patch bump)
- Adding a new optional field with a safe default
- Adding a new enum value (without removing/renaming old ones)
- Adding new documentation or examples
- Adding stricter validation only if old outputs still pass

### Deprecation policy
- Never delete old enum values.
- Mark them as deprecated in docs and stop generating them.
- Keep them valid in schema until a major version rewrite is explicitly approved.

---

## Current Versions (Authoritative)

### Stage 4 — Description Intelligence
- Schema: `stage4_description_intel.schema.json` → **v1.0.0**
- Signal Enums: `docs/STAGE_4_SIGNAL_ENUMS.md` → **v1.0**
- Ruleset Version: **v1.0** (keyword/regex guardrails)
- Prompt Version: **v1.0** (LLM extractor prompt)

### Stage 7 — Price & Deal Intelligence
- Schema: `stage7_price_intel.schema.json` → **TBD**

### Stage 8 — Alternative Recommender
- Schema: `stage8_alternatives.schema.json` → **TBD**

### Stage 9 — Buyer-Ready Summary
- Schema: `stage9_buyer_summary.schema.json` → **TBD**

### Flipability Score
- Schema: `flipability_score.schema.json` → **v1.0.0**

---

## Change Log

### v1.0.0 (Stage 4 schema) — Initial release
- Introduced LLM-primary extraction with evidence verification
- Added Verified vs Inferred semantics
- Added signal categories: legality, accident, mechanical, cosmetic, mods, seller behavior
- Added maintenance section, missing_info, and follow-up questions