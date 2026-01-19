# Deal Intelligence — AI Pipeline

AI-powered deal intelligence system for Facebook Marketplace vehicle listings.

This repository implements **Stages 4-9** of the deal intelligence pipeline, which runs after scraping to extract structured intelligence, estimate prices, find alternatives, and generate buyer-ready summaries.

## Overview

The AI pipeline converts raw listing data into actionable intelligence:

- **Stage 4:** Description Intelligence — Extract structured signals from listing text
- **Stage 7:** Price Intelligence — Estimate fair market value and deal quality
- **Stage 8:** Alternatives — Find better or similar options
- **Stage 9:** Buyer Summary — Generate user-facing recommendations

## Repository Structure

```
.
├── docs/                    # Documentation for humans and AI
├── contracts/               # Schema definitions (prevent breaking changes)
├── stages/                  # Individual stage implementations
├── common/                  # Shared concepts and guidelines
└── data_samples/            # Example data for testing
```

See `/docs/REPO_STRUCTURE_AI.md` and `/REPO_STRUCTURE.md` for detailed structure.

## Quick Start

1. **Run the pipeline:** `python3 quick_test.py`
2. **Read the docs:**
   - [`ARCHITECTURE.md`](ARCHITECTURE.md) - System design and pipeline flow
   - [`CODE_DOCUMENTATION.md`](CODE_DOCUMENTATION.md) - API reference and module docs
   - [`TESTING.md`](TESTING.md) - Testing guide and test suite
   - [`CONTRIBUTING.md`](CONTRIBUTING.md) - How to contribute

3. **Explore the notebook:** `jupyter notebook notebooks/stage4_poc.ipynb`

**Original Documentation:**
- `/docs/AI_PIPELINE_OVERVIEW.md` - High-level system overview
- `/docs/STAGE_4_IMPLEMENTATION.md` - Stage 4 implementation details
- `/docs/STAGE_OUTPUT_CONTRACTS.md` - Input/output contracts

## Golden Rules

1. **Pure Functions:** Each stage is pure — same inputs → same outputs
2. **Idempotent:** Re-running stages is safe and deterministic
3. **Evidence Required:** Every signal must have evidence text spans
4. **LLMs Extract, Don't Invent:** LLMs extract facts from text, they don't create them

## Development

- Stage contracts are in `/contracts/` — don't break them
- Shared concepts are in `/common/` — reuse them
- Each stage is isolated in `/stages/{stage_name}/` — keep them independent

## Status

- **Stage 4:** ✅ **Implemented** (66 tests passing)
  - LLM-primary extraction with guardrails
  - Evidence verification
  - Schema validation
  - See [`TESTING.md`](TESTING.md) for test details
- **Stage 7-9:** Planned (see individual stage READMEs)

## Documentation

| Document | Description |
|----------|-------------|
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System architecture, pipeline flow, component design |
| [`CODE_DOCUMENTATION.md`](CODE_DOCUMENTATION.md) | API reference, module documentation, type hints |
| [`TESTING.md`](TESTING.md) | Testing guide, test suites, coverage |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Development workflow, code standards, PR guidelines |
| [`TESTING_GUIDE.md`](TESTING_GUIDE.md) | Quick testing reference |

## Quick Start

### Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Run Quick Test

```bash
python quick_test.py
```

This runs the pipeline on a sample listing with guardrails-only mode (no API key required).

---

For detailed implementation guidance, see the documentation in `/docs/`.
