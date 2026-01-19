"""
Stage 4 Pipeline Runner

Orchestrates the full Stage 4 extraction pipeline:
1. Input validation
2. Text preparation
3. LLM extraction
4. Evidence verification
5. Guardrail rules
6. Signal merging
7. Derived field computation
8. Schema validation

Includes comprehensive logging and metrics collection.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import (
    STAGE_VERSION,
    RULESET_VERSION,
    DEFAULT_MODEL,
    SHORT_DESCRIPTION_THRESHOLD,
)
from stage4.text_prep import normalize_text, PreparedText
from stage4.llm_extractor import extract_with_llm, create_fallback_output
from stage4.evidence_verifier import verify_signals
from stage4.guardrails import run_guardrails, check_high_risk_keywords
from stage4.merger import merge_signals, merge_maintenance
from stage4.derived_fields import compute_derived_fields
from stage4.schema_validator import validate_stage4_output, validate_or_raise
from stage4.normalizer import normalize_missing_info_list
from common.metrics import (
    get_metrics,
    timer,
    increment,
    histogram,
    record_extraction_metrics,
    record_signal_metrics,
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """
    Result container for pipeline execution.
    
    Provides structured access to output, errors, and metadata.
    """
    success: bool
    output: Optional[Dict[str, Any]]
    error: Optional[Exception] = None
    warnings: List[str] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metrics is None:
            self.metrics = {}


def run_stage4(
    listing: Dict[str, Any],
    source_snapshot_id: Optional[str] = None,
    skip_llm: bool = False,
    model: str = DEFAULT_MODEL,
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Run the complete Stage 4 pipeline on a listing.
    
    Args:
        listing: Raw listing dictionary with at minimum:
            - listing_id
            - title
            - description
        source_snapshot_id: Optional snapshot ID (defaults to listing_id)
        skip_llm: If True, only run guardrail rules (for testing)
        model: OpenAI model to use
        validate: If True, validate output against schema
        
    Returns:
        Stage 4 output dictionary (schema-valid)
        
    Raises:
        ValidationError: If validate=True and output fails validation
    """
    start_time = time.time()
    metrics = get_metrics()
    
    # Extract required fields
    listing_id = str(listing.get("listing_id", "unknown"))
    title = listing.get("title", "") or ""
    description = listing.get("description", "") or ""
    
    logger.info(f"Starting Stage 4 pipeline for listing {listing_id}")
    
    # Optional fields
    vehicle_type = listing.get("vehicle_type", "unknown")
    if vehicle_type not in ["car", "bike", "unknown"]:
        vehicle_type = "unknown"
    
    price = listing.get("price")
    mileage = listing.get("mileage")
    
    # Use listing_id as snapshot_id if not provided
    if source_snapshot_id is None:
        source_snapshot_id = listing_id
    
    # Step 1: Text preparation
    with timer("stage4.text_prep"):
        prepared_text = normalize_text(title, description)
    
    logger.debug(f"Text prepared: {len(prepared_text.combined_text)} chars")
    
    # Step 2: LLM extraction (or fallback)
    llm_start = time.time()
    if skip_llm:
        logger.info(f"Skipping LLM for listing {listing_id}")
        llm_result = create_fallback_output(
            listing_id=listing_id,
            source_snapshot_id=source_snapshot_id,
            title=title,
            description=description,
            warning="LLM skipped (skip_llm=True)",
        )
        llm_latency_ms = None
    else:
        with timer("stage4.llm_extraction"):
            llm_result = extract_with_llm(
                listing_id=listing_id,
                source_snapshot_id=source_snapshot_id,
                title=title,
                description=description,
                vehicle_type=vehicle_type,
                price=price,
                mileage=mileage,
                model=model,
            )
        llm_latency_ms = (time.time() - llm_start) * 1000
        logger.info(f"LLM extraction completed in {llm_latency_ms:.0f}ms")
    
    # Step 3: Evidence verification
    with timer("stage4.evidence_verification"):
        verified_result = verify_signals(llm_result, prepared_text.combined_text)
    
    # Step 4: Guardrail rules
    with timer("stage4.guardrails"):
        rule_signals = run_guardrails(prepared_text)
    
    # Count guardrail detections
    guardrail_count = sum(len(signals) for signals in rule_signals.values())
    logger.info(f"Guardrails detected {guardrail_count} signals")
    
    # Step 5: Merge signals
    with timer("stage4.merge"):
        llm_signals = verified_result.get("payload", {}).get("signals", {})
        merged_signals = merge_signals(llm_signals, rule_signals)
        
        # Merge maintenance
        llm_maintenance = verified_result.get("payload", {}).get("maintenance", {})
        merged_maintenance = merge_maintenance(llm_maintenance, rule_signals)
    
    # Count total signals
    total_signals = sum(len(signals) for signals in merged_signals.values())
    histogram("stage4.signals_per_extraction", total_signals)
    
    # Record signal metrics
    for category, signal_list in merged_signals.items():
        for signal in signal_list:
            record_signal_metrics(
                category=category,
                signal_type=signal.get("type", "unknown"),
                severity=signal.get("severity", "medium"),
                verification_level=signal.get("verification_level", "inferred"),
            )
    
    # Step 6: Compute derived fields
    with timer("stage4.derived_fields"):
        llm_summaries = {
            "claimed_condition": verified_result.get("payload", {}).get("claimed_condition", "unknown"),
            "negotiation_stance": verified_result.get("payload", {}).get("negotiation_stance", "unknown"),
            "service_history_level": verified_result.get("payload", {}).get("service_history_level", "unknown"),
            "mods_risk_level": verified_result.get("payload", {}).get("mods_risk_level", "unknown"),
        }
        
        derived = compute_derived_fields(merged_signals, merged_maintenance, llm_summaries)
    
    logger.info(f"Derived fields: risk={derived['risk_level_overall']}, mods={derived['mods_risk_level']}")
    
    # Step 7: Build final output
    output = build_output(
        listing_id=listing_id,
        source_snapshot_id=source_snapshot_id,
        title=title,
        description=description,
        signals=merged_signals,
        maintenance=merged_maintenance,
        derived=derived,
        llm_result=verified_result,
        model=model if not skip_llm else None,
    )
    
    # Step 8: Validate
    validation_passed = True
    if validate:
        with timer("stage4.validation"):
            try:
                validate_or_raise(output)
                logger.debug("Schema validation passed")
            except Exception as e:
                validation_passed = False
                logger.error(f"Schema validation failed: {e}")
                raise
    
    # Record overall metrics
    total_time_ms = (time.time() - start_time) * 1000
    metrics.timing("stage4.pipeline_total", total_time_ms)
    
    record_extraction_metrics(
        listing_id=listing_id,
        llm_used=not skip_llm,
        llm_latency_ms=llm_latency_ms,
        signals_extracted=total_signals,
        validation_passed=validation_passed,
    )
    
    logger.info(
        f"Stage 4 completed for {listing_id}: "
        f"{total_signals} signals, {total_time_ms:.0f}ms total"
    )
    
    return output


def run_stage4_safe(
    listing: Dict[str, Any],
    source_snapshot_id: Optional[str] = None,
    skip_llm: bool = False,
    model: str = DEFAULT_MODEL,
    validate: bool = True,
) -> PipelineResult:
    """
    Run Stage 4 pipeline with error handling, returning a Result object.
    
    Unlike run_stage4, this never raises exceptions - errors are captured
    in the PipelineResult.
    
    Args:
        listing: Raw listing dictionary
        source_snapshot_id: Optional snapshot ID
        skip_llm: If True, skip LLM extraction
        model: OpenAI model to use
        validate: If True, validate output
        
    Returns:
        PipelineResult with success status, output, and any errors
    """
    listing_id = str(listing.get("listing_id", "unknown"))
    
    try:
        output = run_stage4(
            listing=listing,
            source_snapshot_id=source_snapshot_id,
            skip_llm=skip_llm,
            model=model,
            validate=validate,
        )
        
        warnings = output.get("payload", {}).get("extraction_warnings", [])
        
        return PipelineResult(
            success=True,
            output=output,
            warnings=warnings,
        )
        
    except Exception as e:
        logger.error(f"Pipeline failed for {listing_id}: {e}")
        increment("stage4.pipeline_errors")
        
        # Create fallback output
        fallback = create_fallback_output(
            listing_id=listing_id,
            source_snapshot_id=source_snapshot_id or listing_id,
            title=listing.get("title", ""),
            description=listing.get("description", ""),
            warning=f"Pipeline error: {str(e)}",
        )
        
        return PipelineResult(
            success=False,
            output=fallback,
            error=e,
            warnings=[f"Pipeline error: {str(e)}"],
        )


def build_output(
    listing_id: str,
    source_snapshot_id: str,
    title: str,
    description: str,
    signals: Dict[str, list],
    maintenance: Dict[str, Any],
    derived: Dict[str, str],
    llm_result: Dict[str, Any],
    model: Optional[str],
) -> Dict[str, Any]:
    """
    Build the final Stage 4 output structure.
    
    Args:
        listing_id: Listing identifier
        source_snapshot_id: Snapshot identifier
        title: Original title
        description: Original description
        signals: Merged signals
        maintenance: Merged maintenance
        derived: Derived summary fields
        llm_result: Original LLM result (for missing_info, questions, warnings)
        model: Model used (None if LLM skipped)
        
    Returns:
        Complete Stage 4 output dictionary
    """
    llm_payload = llm_result.get("payload", {})
    
    # Get LLM-generated fields we want to preserve
    # Normalize missing_info to handle unknown types (map to "other")
    missing_info = normalize_missing_info_list(llm_payload.get("missing_info", []))
    follow_up_questions = llm_payload.get("follow_up_questions", [])
    extraction_warnings = llm_payload.get("extraction_warnings", [])
    
    # Add warning if description is short
    if len(description) < SHORT_DESCRIPTION_THRESHOLD:
        extraction_warnings.append(
            f"Description is very short ({len(description)} chars)"
        )
    
    # Build source text stats
    combined_text = f"{title}\n{description}"
    source_text_stats = {
        "title_length": len(title),
        "description_length": len(description),
        "contains_keywords_high_risk": check_high_risk_keywords(combined_text),
    }
    
    return {
        "listing_id": listing_id,
        "source_snapshot_id": source_snapshot_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stage_name": "stage4_description_intelligence",
        "stage_version": STAGE_VERSION,
        "ruleset_version": RULESET_VERSION,
        "llm_version": model,
        "payload": {
            "risk_level_overall": derived["risk_level_overall"],
            "negotiation_stance": derived["negotiation_stance"],
            "claimed_condition": derived["claimed_condition"],
            "service_history_level": derived["service_history_level"],
            "mods_risk_level": derived["mods_risk_level"],
            "signals": signals,
            "maintenance": maintenance,
            "missing_info": missing_info,
            "follow_up_questions": follow_up_questions,
            "extraction_warnings": extraction_warnings,
            "source_text_stats": source_text_stats,
        },
    }


def run_stage4_batch(
    listings: List[Dict[str, Any]],
    skip_llm: bool = False,
    model: str = DEFAULT_MODEL,
    validate: bool = True,
) -> List[PipelineResult]:
    """
    Run Stage 4 on a batch of listings.
    
    Args:
        listings: List of listing dictionaries
        skip_llm: If True, only run guardrail rules
        model: OpenAI model to use
        validate: If True, validate each output
        
    Returns:
        List of PipelineResult objects
    """
    logger.info(f"Starting batch processing of {len(listings)} listings")
    start_time = time.time()
    
    results = []
    success_count = 0
    error_count = 0
    
    for i, listing in enumerate(listings):
        listing_id = listing.get("listing_id", f"batch_{i}")
        logger.debug(f"Processing listing {i+1}/{len(listings)}: {listing_id}")
        
        result = run_stage4_safe(
            listing=listing,
            skip_llm=skip_llm,
            model=model,
            validate=validate,
        )
        results.append(result)
        
        if result.success:
            success_count += 1
        else:
            error_count += 1
    
    total_time = time.time() - start_time
    avg_time = total_time / len(listings) if listings else 0
    
    logger.info(
        f"Batch complete: {success_count} succeeded, {error_count} failed, "
        f"{total_time:.1f}s total ({avg_time:.2f}s avg)"
    )
    
    # Record batch metrics
    increment("stage4.batch_runs")
    histogram("stage4.batch_size", len(listings))
    histogram("stage4.batch_success_rate", success_count / len(listings) if listings else 0)
    
    return results


def run_guardrails_only(listing: Dict[str, Any]) -> Dict[str, list]:
    """
    Run only guardrail rules without LLM (for testing).
    
    Args:
        listing: Listing dictionary
        
    Returns:
        Signals dictionary from guardrails
    """
    title = listing.get("title", "") or ""
    description = listing.get("description", "") or ""
    
    prepared_text = normalize_text(title, description)
    return run_guardrails(prepared_text)
