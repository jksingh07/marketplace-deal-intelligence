# Deal Intelligence — AI Pipeline

AI-powered deal intelligence system for Facebook Marketplace vehicle listings.

This repository implements **Stages 4-9** of the deal intelligence pipeline, which runs after scraping to extract structured intelligence, estimate prices, find alternatives, and generate buyer-ready summaries.

## Overview

The AI pipeline converts raw listing data into actionable intelligence:

- **Stage 4:** Description Intelligence — Extract structured signals from listing text (✅ **Production-Ready**)
- **Stage 7:** Price Intelligence — Estimate fair market value and deal quality (Planned)
- **Stage 8:** Alternatives — Find better or similar options (Planned)
- **Stage 9:** Buyer Summary — Generate user-facing recommendations (Planned)

## Key Features

### Production-Ready Architecture

✅ **Resilient by Design** - Unknown LLM outputs map to "other" instead of failing  
✅ **Centralized Enums** - Single source of truth for all type definitions  
✅ **Normalization Layer** - Gracefully handles LLM output variations  
✅ **Structured Outputs** - JSON mode for schema-constrained responses  
✅ **Observability** - Structured logging and metrics collection  
✅ **Async Support** - Non-blocking LLM calls for scalability  
✅ **Rate Limiting** - Prevents API quota exhaustion  
✅ **Circuit Breaker** - Prevents cascading failures  
✅ **Result Caching** - Optimizes repeated processing  
✅ **Input Validation** - Sanitizes and validates inputs  

### Intelligent Extraction

- **Evidence-Based** - Every signal is backed by verbatim source text
- **Dual-Mode Detection** - Deterministic rules (guaranteed) + AI (comprehensive)
- **Risk Scoring** - Automatic risk assessment (low/medium/high)
- **Schema-Validated** - All outputs conform to JSON Schema contracts

## Repository Structure

```
.
├── src/                       # Source code
│   ├── common/               # Shared utilities
│   │   ├── schema_enums.py   # Centralized enum definitions
│   │   ├── normalizer.py     # Value normalization
│   │   ├── logging_config.py # Structured logging
│   │   ├── metrics.py        # Metrics collection
│   │   ├── rate_limiter.py   # API rate limiting
│   │   ├── circuit_breaker.py # Failure handling
│   │   ├── caching.py        # Result caching
│   │   ├── input_validation.py # Input sanitization
│   │   └── models.py         # Pydantic models
│   └── stage4/               # Stage 4 implementation
│       ├── runner.py         # Pipeline orchestrator
│       ├── text_prep.py      # Text normalization
│       ├── llm_extractor.py  # LLM integration (sync)
│       ├── llm_extractor_async.py # LLM integration (async)
│       ├── guardrails.py     # Rule-based detection
│       ├── evidence_verifier.py # Evidence validation
│       ├── normalizer.py     # Signal normalization
│       ├── merger.py         # Signal merging
│       ├── derived_fields.py # Risk calculation
│       └── schema_validator.py # Output validation
├── contracts/                # JSON Schema contracts
├── stages/                   # Stage-specific docs/rules
├── docs/                     # Documentation
├── tests/                    # Test suite (66 tests)
├── notebooks/                # POC and demos
└── data_samples/             # Example data
```

See `/docs/REPO_STRUCTURE_AI.md` and `/REPO_STRUCTURE.md` for detailed structure.

## Quick Start

1. **Setup:**
   ```bash
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   
   # Install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Run the pipeline:**
   ```bash
   python3 quick_test.py
   ```
   This runs with guardrails-only mode (no API key required).

3. **Run with LLM (optional):**
   ```bash
   # Create .env file in project root
   echo "OPENAI_API_KEY=your-key-here" > .env
   
   # Run again - LLM extraction will be enabled
   python3 quick_test.py
   ```

4. **Run tests:**
   ```bash
   pytest tests/ -v
   # All 66 tests should pass
   ```

5. **Explore the notebook:**
   ```bash
   jupyter notebook notebooks/stage4_poc.ipynb
   ```
   Investor-friendly demo with detailed explanations.

## Documentation

| Document | Description |
|----------|-------------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System architecture, pipeline flow, production-ready modules |
| [`CODE_DOCUMENTATION.md`](CODE_DOCUMENTATION.md) | API reference, module documentation, type hints |
| [`TESTING.md`](TESTING.md) | Testing guide, test suites, coverage |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Development workflow, code standards, PR guidelines |
| [`TESTING_GUIDE.md`](TESTING_GUIDE.md) | Quick testing reference |

## Golden Rules

1. **Pure Functions** - Each stage is pure — same inputs → same outputs
2. **Idempotent** - Re-running stages is safe and deterministic
3. **Evidence Required** - Every signal must have evidence text spans
4. **LLMs Extract, Don't Invent** - LLMs extract facts from text, they don't create them
5. **Resilient by Design** - Unknown types map to "other", never fail on variations
6. **Schema-Valid Always** - Outputs always conform to JSON Schema contract

## Status

### Stage 4: ✅ **Production-Ready**

**Implementation Status:**
- ✅ LLM-primary extraction with guardrails
- ✅ Evidence verification (verbatim text matching)
- ✅ Schema validation
- ✅ Resilient normalization (handles unknown types)
- ✅ Structured outputs (JSON mode)
- ✅ Async support for scalability
- ✅ Observability (logging, metrics)
- ✅ Production hardening (rate limiting, circuit breaker, caching)

**Test Coverage:**
- 66 tests passing
- Idempotency verified
- Schema validation tested
- Evidence verification tested
- Guardrail rules tested

**See [`TESTING.md`](TESTING.md) for test details**

### Stages 7-9: Planned

See individual stage READMEs in `/stages/` for implementation status.

## Architectural Highlights

### Resilient Design

The system is designed to **never reject valid semantic content** from LLM outputs. Unknown types are gracefully mapped to `"other"` instead of causing validation failures. This ensures:

- No data loss from LLM variations
- Production stability even with unexpected inputs
- Graceful degradation without breaking

### Production-Ready Modules

- **`schema_enums.py`** - Single source of truth for all enum definitions
- **`normalizer.py`** - Centralized value mapping and normalization
- **`metrics.py`** - Thread-safe metrics collection
- **`rate_limiter.py`** - Token bucket rate limiting
- **`circuit_breaker.py`** - Failure handling with state machine
- **`caching.py`** - LRU cache with TTL support
- **`input_validation.py`** - Input sanitization and validation
- **`logging_config.py`** - Structured JSON logging

### Scalability Features

- **Async LLM Calls** - Non-blocking API requests
- **Batch Processing** - Concurrent listing analysis
- **Result Caching** - Avoids redundant processing
- **Rate Limiting** - Prevents API quota exhaustion

## Development

- **Stage contracts** are in `/contracts/` — don't break them
- **Shared utilities** are in `/src/common/` — reuse them
- **Each stage** is isolated — keep them independent
- **Tests** must pass before merging
- **Schema validation** is non-negotiable

## Environment Variables

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your-openai-api-key-here
```

This enables LLM extraction. Without it, the system runs in guardrails-only mode.

## License

[Add your license here]

---

For detailed implementation guidance, see the documentation in `/docs/` and individual stage READMEs.
