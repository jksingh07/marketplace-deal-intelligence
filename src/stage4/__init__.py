"""
Stage 4: Description Intelligence

Extracts structured, evidence-backed intelligence from listing text
using an LLM-primary pipeline with deterministic safety guardrails.

Includes:
- Runner: Main pipeline orchestration
- Text Prep: Text normalization
- LLM Extractor: OpenAI integration with structured outputs
- Evidence Verifier: Verbatim evidence validation
- Guardrails: Rule-based signal detection
- Merger: Signal merging
- Normalizer: Value normalization
- Derived Fields: Summary computation
- Schema Validator: Output validation
"""

from stage4.runner import run_stage4, run_stage4_safe, run_stage4_batch, PipelineResult
from stage4.text_prep import normalize_text, split_sentences
from stage4.llm_extractor import extract_with_llm
from stage4.evidence_verifier import verify_signals
from stage4.guardrails import run_guardrails
from stage4.merger import merge_signals
from stage4.normalizer import (
    SignalNormalizer,
    normalize_signal_type,
    normalize_signals,
    normalize_maintenance,
)
from stage4.derived_fields import compute_derived_fields
from stage4.schema_validator import validate_stage4_output

__all__ = [
    # Runner
    "run_stage4",
    "run_stage4_safe",
    "run_stage4_batch",
    "PipelineResult",
    # Text prep
    "normalize_text",
    "split_sentences",
    # LLM
    "extract_with_llm",
    # Evidence
    "verify_signals",
    # Guardrails
    "run_guardrails",
    # Merger
    "merge_signals",
    # Normalizer
    "SignalNormalizer",
    "normalize_signal_type",
    "normalize_signals",
    "normalize_maintenance",
    # Derived
    "compute_derived_fields",
    # Validation
    "validate_stage4_output",
]
