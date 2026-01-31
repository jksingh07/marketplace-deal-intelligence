# Architecture Documentation

## System Overview

Stage 4 Description Intelligence is a **LLM-primary extraction pipeline with deterministic guardrails** that converts raw listing text into structured, evidence-backed intelligence signals.

### Design Philosophy

1. **LLM is the Primary Extractor** - LLMs handle nuanced extraction and context understanding
2. **Guardrails Never Fail** - Rule-based patterns catch critical signals even if LLM fails
3. **Evidence is Required** - Every signal must be traceable to source text
4. **Schema-Valid Always** - Outputs always conform to JSON Schema contract
5. **Idempotent by Design** - Same inputs produce identical outputs
6. **Resilient by Design** - Unknown LLM outputs map to `"other"` instead of failing (prevents data loss)

---

## Pipeline Architecture

### High-Level Flow

```
Raw Listing (title + description)
    │
    ├─→ [Text Preparation]
    │      │
    │      ├─→ Normalize text (whitespace, casing)
    │      ├─→ Split into sentences
    │      └─→ Preserve original for evidence matching
    │
    ├─→ [Guardrail Rules] ─────┐
    │      │                   │
    │      └─→ Pattern matching │ (ALWAYS RUNS)
    │          (write-off,      │
    │           defected,       │
    │           stage 2, etc.)  │
    │                           │
    └─→ [LLM Extraction] ───────┤
         │                      │
         └─→ OpenAI API call    │
             Structured JSON    │
                                │
                                ▼
                    [Evidence Verification]
                         │
                         ├─→ Check evidence_text exists verbatim
                         ├─→ Reject hallucinations
                         └─→ Classify verified vs inferred
                                │
                                ▼
                         [Signal Merger]
                         │
                         ├─→ Combine LLM + guardrail signals
                         ├─→ Deduplicate by (type, evidence)
                         └─→ Prefer guardrail confidence on conflicts
                                │
                                ▼
                         [Derived Fields]
                         │
                         ├─→ risk_level_overall
                         ├─→ mods_risk_level
                         ├─→ negotiation_stance
                         └─→ service_history_level
                                │
                                ▼
                         [Schema Validation]
                         │
                         └─→ Ensure JSON Schema compliance
                                │
                                ▼
                    Final Output (Stage 4 JSON)
```

---

## Component Architecture

### 1. Text Preparation (`text_prep.py`)

**Purpose:** Normalize and prepare text for extraction while preserving original for evidence.

**Key Functions:**
- `normalize_text()` - Combines title + description, normalizes whitespace
- `split_sentences()` - Tokenizes text into sentences for evidence extraction
- `find_evidence_span()` - Extracts context around keywords for evidence

**Design Decisions:**
- Preserves original casing for evidence matching
- Lowercases normalized version for pattern matching
- Sentence splitting enables precise evidence spans

### 2. Guardrail Rules (`guardrails.py`)

**Purpose:** Deterministic pattern matching for high-severity signals.

**Coverage:**
- **Legality:** defected, unregistered, no rego, no RWC
- **Accident History:** write-off, salvage, flood damage
- **Mechanical:** not running, overheating, engine knock
- **Performance Mods:** stage 2+, E85, turbo swap, track use
- **Seller Behavior:** firm price, urgent sale

**Properties:**
- Always `verification_level=verified`
- Always `confidence=0.95`
- Evidence text is exact substring match
- Never removed by LLM output (rules win conflicts)

### 3. LLM Extractor (`llm_extractor.py`)

**Purpose:** Structured extraction using OpenAI GPT models.

**Features:**
- Loads prompt from `stages/stage4_description_intel/prompts/extractor_prompt.md`
- Retries with exponential backoff (3 attempts)
- Handles malformed JSON gracefully
- Falls back to minimal structure if LLM fails

**Output Structure:**
- Matches Stage 4 schema exactly
- All signals have evidence_text
- All enums match contract definitions

### 4. Evidence Verifier (`evidence_verifier.py`)

**Purpose:** Validate that all signals have verbatim evidence in source text.

**Verification Rules:**
- Evidence text must exist in original text (case-insensitive)
- Rejects signals without valid evidence
- Classifies as `verified` (explicit) or `inferred` (implicit wording)
- Adjusts confidence based on verification level

**Safety:** Prevents hallucination by requiring exact substring matches.

### 5. Signal Merger (`merger.py`)

**Purpose:** Combine LLM and guardrail signals without duplicates.

**Merge Strategy:**
- Union both signal sets
- Deduplicate by `(type, evidence_text)`
- If conflict: Prefer guardrail signal (higher confidence)
- Preserve verification levels from both sources

**Maintenance:** Deduplicates claims and red flags separately.

### 6. Derived Fields (`derived_fields.py`)

**Purpose:** Compute summary fields from extracted signals (rule-based, not LLM).

**Computed Fields:**

| Field | Logic |
|-------|-------|
| `risk_level_overall` | HIGH if any HIGH severity verified; MEDIUM if multiple medium; LOW otherwise |
| `mods_risk_level` | HIGH: stage 2+, turbo swap, E85, track use; MEDIUM: tuned, intake/exhaust; LOW: cosmetic |
| `service_history_level` | FULL: logbook + receipts; PARTIAL: claims without proof; NONE: explicit "no history" |
| `negotiation_stance` | FIRM: "firm price", "no lowballers"; OPEN: "negotiable", "need gone" |
| `claimed_condition` | EXCELLENT → GOOD → FAIR → NEEDS_WORK based on signals |

**Design:** Deterministic computations ensure idempotency.

### 7. Schema Validator (`schema_validator.py`)

**Purpose:** Validate final output against JSON Schema contract.

**Validation:**
- Loads schema from `contracts/stage4_description_intel.schema.json`
- Validates all required fields present
- Validates enum values match schema
- Validates confidence in [0, 1]
- Validates evidence_text non-empty

**On Failure:** Raises detailed error with field paths and messages.

### 8. Pipeline Runner (`runner.py`)

**Purpose:** Orchestrate all stages in correct order.

**Pipeline Steps:**
1. Extract listing fields (with defaults)
2. Text preparation
3. LLM extraction (or fallback)
4. Evidence verification
5. Guardrail rules
6. Signal merging
7. Derived field computation
8. Build final output structure
9. Schema validation (optional)

**Idempotency:** Same listing + snapshot_id = identical output structure.

---

## Data Flow

### Input Format

```python
listing = {
    "listing_id": "12345",
    "title": "2015 Subaru WRX STI",
    "description": "Stage 2 tune, defected for exhaust...",
    "vehicle_type": "car",  # Optional, defaults to "unknown"
    "price": 25000,  # Optional
    "mileage": 50000,  # Optional
}
```

### Output Format

```json
{
  "listing_id": "12345",
  "source_snapshot_id": "12345",
  "created_at": "2024-01-18T12:00:00Z",
  "stage_name": "stage4_description_intelligence",
  "stage_version": "v1.0.0",
  "ruleset_version": "v1.0",
  "llm_version": "gpt-4o-mini",
  "payload": {
    "risk_level_overall": "high",
    "negotiation_stance": "open",
    "claimed_condition": "fair",
    "service_history_level": "unknown",
    "mods_risk_level": "high",
    "signals": {
      "legality": [{...}],
      "accident_history": [{...}],
      "mechanical_issues": [{...}],
      "cosmetic_issues": [{...}],
      "mods_performance": [{...}],
      "mods_cosmetic": [{...}],
      "seller_behavior": [{...}]
    },
    "maintenance": {
      "claims": [...],
      "evidence_present": [...],
      "red_flags": [...]
    },
    "missing_info": [...],
    "follow_up_questions": [...],
    "extraction_warnings": [...],
    "source_text_stats": {...}
  }
}
```

---

## Design Patterns

### 1. Guardrail-First Safety

Guardrails **always run** regardless of LLM status. This ensures:
- Critical signals (write-off, defected) are never missed
- Pipeline works even if LLM is unavailable
- High-severity patterns have 100% detection rate

### 2. Evidence-Based Verification

Every signal requires verbatim evidence text:
- Prevents hallucination
- Enables traceability
- Supports confidence scoring

### 3. Deterministic Merging

Merge logic is rule-based:
- No randomness in signal combination
- Idempotent output structure
- Predictable conflict resolution (rules win)

### 4. Fail-Safe Fallbacks

- LLM fails → Return rules-only output
- Invalid JSON → Return minimal valid structure
- Schema validation → Raise clear error (don't mask)

### 5. Schema-Driven Development

- Output contract defined in JSON Schema
- Code validates against schema
- Schema changes trigger validation updates

---

## Performance Characteristics

### Latency (Guardrails-Only)

- Text prep: < 1ms
- Guardrail rules: < 5ms
- Derived fields: < 1ms
- Schema validation: < 10ms
- **Total: < 20ms per listing**

### Latency (With LLM)

- LLM API call: 1-3 seconds (depending on model)
- Evidence verification: < 10ms
- Other steps: same as guardrails-only
- **Total: 1-3 seconds per listing**

### Throughput

- Guardrails-only: ~50 listings/second (CPU-bound)
- With LLM: Limited by OpenAI rate limits (varies by tier)

---

## Error Handling

### LLM Failures

- Timeout/rate limit → Retry 3x with exponential backoff
- Invalid JSON → Return fallback structure with warning
- API error → Return rules-only output

### Validation Failures

- Schema mismatch → Raise `ValidationError` with details
- Missing fields → Fail fast with clear message
- Invalid enums → Validation error with field path

### Evidence Failures

- Missing evidence → Signal rejected (not in output)
- Partial match → Treated as inferred (lower confidence)

---

## Extensibility

### Adding New Guardrail Rules

Edit `src/stage4/guardrails.py`:

```python
NEW_RULE = (r'\bnew_pattern\b', 'signal_type', 'category', 'severity')
ALL_RULES = ALL_RULES + [NEW_RULE]
```

### Adding New Signal Types

1. Add enum to `src/common/models.py`
2. Update schema in `contracts/stage4_description_intel.schema.json`
3. Update prompt template if LLM should extract it

### Adding New Derived Fields

Edit `src/stage4/derived_fields.py`:

```python
def compute_new_field(signals, ...) -> str:
    # Deterministic logic
    return "value"
```

Then add to `compute_derived_fields()` return dict.

---

## Security Considerations

### API Key Management

- `OPENAI_API_KEY` loaded from environment variable
- Never logged or exposed in outputs
- Use `.env` file locally (gitignored)

### Input Validation

- Sanitize listing text (prevent injection)
- Validate listing_id format
- Limit input text length (prevent DoS)

### Output Sanitization

- All outputs are JSON (structured)
- No executable code in outputs
- Evidence text is verbatim from input (no code injection)

---

## Production-Ready Modules

The pipeline includes the following production-hardened modules:

### 1. Centralized Enums (`common/schema_enums.py`)

Single source of truth for all enum definitions, loaded dynamically from the JSON schema.
Prevents drift between schema and code.

### 2. Signal Normalizer (`stage4/normalizer.py`)

Gracefully handles LLM output variations by mapping common alternatives to valid schema values.
**Key Design Principle**: Unknown types map to `"other"` instead of being rejected, ensuring no data loss.

**Examples:**
- `"write_off"` → `"writeoff"`
- `"service_history"` → `"logbook"`
- `"service_history_none"` → `"service_history_unknown"`
- `"rwc_status_unknown"` → `"other"` (preserved, not rejected)

**Architectural Benefit**: Makes the system resilient to LLM variations without breaking production.

### 3. Structured Logging (`common/logging_config.py`)

JSON-structured logging for production environments, with human-readable format for development.

### 4. Metrics Collection (`common/metrics.py`)

Thread-safe metrics collection for monitoring:
- Counters, gauges, histograms, timers
- Per-extraction metrics (latency, tokens, signals)
- Ready for Prometheus/DataDog integration

### 5. Rate Limiting (`common/rate_limiter.py`)

Token bucket rate limiter for API calls:
- Configurable calls per minute/second
- Burst support
- Async support

### 6. Circuit Breaker (`common/circuit_breaker.py`)

Prevents cascading failures when external services are down:
- CLOSED → OPEN → HALF_OPEN state machine
- Configurable thresholds and timeouts
- Sync and async support

### 7. Result Caching (`common/caching.py`)

LRU cache with TTL for expensive operations:
- Guardrails cache (24hr TTL, deterministic)
- LLM cache (1hr TTL)
- Thread-safe

### 8. Input Validation (`common/input_validation.py`)

Validates and sanitizes input before processing:
- Length limits (prevent DoS)
- Required field checks
- Content sanitization

### 9. Async LLM (`stage4/llm_extractor_async.py`)

Non-blocking LLM extraction for concurrent processing:
- AsyncOpenAI client
- Batch extraction with semaphore-controlled concurrency

---

## Resilient Design Pattern

### Problem Solved

**Original Issue**: LLMs are probabilistic and produce variations. Strict enum validation caused:
- Validation failures on unknown types
- Data loss when LLM used valid semantic variations
- Production instability with new LLM outputs
- Rigid system that broke on edge cases

### Solution: "Other" Fallback Pattern

**All enum types include `"other"` as a valid value:**
- `signal_legality_type`: includes `"other"`
- `signal_accident_type`: includes `"other"`
- `signal_mechanical_type`: includes `"other"`
- `maintenance_claim_type`: includes `"other"`
- `maintenance_red_flag_type`: includes `"other"`
- `missing_info`: includes `"other"`

**Normalization Layer:**
- Maps known variations to valid types (e.g., `"write_off"` → `"writeoff"`)
- Maps unknown types to `"other"` instead of rejecting
- Preserves all valid semantic content from LLM

**Result**: 
- ✅ No data loss from LLM variations
- ✅ Production stability with unexpected inputs
- ✅ Graceful degradation without breaking
- ✅ System handles any LLM output

**Trade-off**: Some signals may be categorized as `"other"`, but this is preferable to losing all information.

---

## Current Implementation Status

### ✅ Completed

1. **JSON Mode**: Using OpenAI JSON mode for structured responses
2. **Async Support**: Async LLM extraction for concurrent processing
3. **Structured Logging**: JSON logs for production environments
4. **Metrics Collection**: Thread-safe metrics for monitoring
5. **Rate Limiting**: Token bucket rate limiter
6. **Circuit Breaker**: Failure handling with state machine
7. **Result Caching**: LRU cache with TTL
8. **Input Validation**: Sanitization and validation
9. **Resilient Normalization**: Unknown types → "other" pattern
10. **Centralized Enums**: Single source of truth from schema

### 🚧 Future Enhancements

1. **OpenAI Structured Outputs (Strict)**: Use strict JSON schema mode when available
2. **A/B Testing**: Compare LLM models for quality
3. **Distributed Caching**: Redis integration for multi-instance deployments
4. **Prompt Versioning**: Track prompt versions for reproducibility
5. **Model Fallback Chain**: Automatic fallback to cheaper models on errors
6. **Batch Optimization**: Optimize token usage with batching strategies

---

## Related Documentation

- **Code Details:** See `CODE_DOCUMENTATION.md`
- **Testing:** See `TESTING.md`
- **Contributing:** See `CONTRIBUTING.md`
- **Stage Contracts:** See `docs/STAGE_OUTPUT_CONTRACTS.md`
