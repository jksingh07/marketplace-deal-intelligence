"""
Schema Validator Module for Stage 4

Validates Stage 4 output against the JSON Schema contract.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import jsonschema
from jsonschema import Draft202012Validator, ValidationError

from config import STAGE4_SCHEMA_PATH


_schema_cache: Optional[dict] = None


def load_schema() -> dict:
    """
    Load the Stage 4 JSON Schema from file.
    
    Caches the schema after first load.
    
    Returns:
        Schema dictionary
        
    Raises:
        FileNotFoundError: If schema file not found
    """
    global _schema_cache
    
    if _schema_cache is not None:
        return _schema_cache
    
    if not STAGE4_SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Stage 4 schema not found at {STAGE4_SCHEMA_PATH}"
        )
    
    with open(STAGE4_SCHEMA_PATH) as f:
        _schema_cache = json.load(f)
    
    return _schema_cache


def validate_stage4_output(output: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate Stage 4 output against the schema.
    
    Args:
        output: Stage 4 output dictionary
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    schema = load_schema()
    
    validator = Draft202012Validator(schema)
    
    errors = list(validator.iter_errors(output))
    
    if not errors:
        return True, []
    
    error_messages = []
    for error in errors:
        path = " -> ".join(str(p) for p in error.absolute_path) or "root"
        error_messages.append(f"{path}: {error.message}")
    
    return False, error_messages


def validate_or_raise(output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate Stage 4 output, raising on failure.
    
    Args:
        output: Stage 4 output dictionary
        
    Returns:
        The validated output (unchanged)
        
    Raises:
        ValidationError: If validation fails
    """
    is_valid, errors = validate_stage4_output(output)
    
    if not is_valid:
        error_msg = "Schema validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValidationError(error_msg)
    
    return output


def validate_signal(signal: Dict[str, Any], signal_type: str) -> Tuple[bool, List[str]]:
    """
    Validate a single signal object.
    
    Args:
        signal: Signal dictionary
        signal_type: Type of signal (for enum validation)
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Required fields
    required = ["type", "severity", "verification_level", "evidence_text", "confidence"]
    for field in required:
        if field not in signal:
            errors.append(f"Missing required field: {field}")
    
    # Type validation
    if "type" in signal and not isinstance(signal["type"], str):
        errors.append("'type' must be a string")
    
    # Severity validation
    valid_severities = ["low", "medium", "high"]
    if "severity" in signal and signal["severity"] not in valid_severities:
        errors.append(f"Invalid severity: {signal['severity']}")
    
    # Verification level validation
    valid_verification = ["verified", "inferred"]
    if "verification_level" in signal and signal["verification_level"] not in valid_verification:
        errors.append(f"Invalid verification_level: {signal['verification_level']}")
    
    # Evidence text validation
    if "evidence_text" in signal:
        if not isinstance(signal["evidence_text"], str):
            errors.append("'evidence_text' must be a string")
        elif len(signal["evidence_text"]) < 1:
            errors.append("'evidence_text' must not be empty")
    
    # Confidence validation
    if "confidence" in signal:
        conf = signal["confidence"]
        if not isinstance(conf, (int, float)):
            errors.append("'confidence' must be a number")
        elif conf < 0 or conf > 1:
            errors.append(f"'confidence' must be between 0 and 1, got {conf}")
    
    return len(errors) == 0, errors


def get_schema_version() -> str:
    """
    Get the version of the loaded schema.
    
    Returns:
        Schema version string or "unknown"
    """
    schema = load_schema()
    return schema.get("$id", "unknown").split("/")[-1].replace(".schema.json", "")


def get_required_fields() -> List[str]:
    """
    Get list of required top-level fields.
    
    Returns:
        List of required field names
    """
    schema = load_schema()
    return schema.get("required", [])


def get_payload_required_fields() -> List[str]:
    """
    Get list of required payload fields.
    
    Returns:
        List of required payload field names
    """
    schema = load_schema()
    payload_schema = schema.get("properties", {}).get("payload", {})
    return payload_schema.get("required", [])


def create_minimal_valid_output(
    listing_id: str,
    source_snapshot_id: str,
    stage_version: str = "v1.0.0",
    ruleset_version: str = "v1.0",
) -> Dict[str, Any]:
    """
    Create a minimal schema-valid output structure.
    
    Useful for testing and fallback scenarios.
    
    Args:
        listing_id: Listing identifier
        source_snapshot_id: Snapshot identifier
        stage_version: Stage version
        ruleset_version: Ruleset version
        
    Returns:
        Minimal valid output dictionary
    """
    from datetime import datetime, timezone
    
    return {
        "listing_id": listing_id,
        "source_snapshot_id": source_snapshot_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stage_name": "stage4_description_intelligence",
        "stage_version": stage_version,
        "ruleset_version": ruleset_version,
        "llm_version": None,
        "payload": {
            "risk_level_overall": "unknown",
            "negotiation_stance": "unknown",
            "claimed_condition": "unknown",
            "service_history_level": "unknown",
            "mods_risk_level": "unknown",
            "signals": {
                "legality": [],
                "accident_history": [],
                "mechanical_issues": [],
                "cosmetic_issues": [],
                "mods_performance": [],
                "mods_cosmetic": [],
                "seller_behavior": [],
            },
            "maintenance": {
                "claims": [],
                "evidence_present": [],
                "red_flags": [],
            },
            "missing_info": [],
            "follow_up_questions": [],
            "extraction_warnings": [],
            "source_text_stats": {
                "title_length": 0,
                "description_length": 0,
                "contains_keywords_high_risk": False,
            },
        },
    }
