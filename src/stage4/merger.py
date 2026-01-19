"""
Signal Merger Module for Stage 4

Combines LLM-extracted signals with guardrail-detected signals.
Rules always win for high-risk signals.

Uses centralized normalization from stage4.normalizer.
"""

import logging
from typing import Any, Dict, List, Tuple

from common.schema_enums import get_evidence_present_types
from stage4.normalizer import (
    get_normalizer,
    normalize_maintenance as normalize_maintenance_via_normalizer,
)

# Configure logging
logger = logging.getLogger(__name__)

# Valid evidence types loaded from schema
VALID_EVIDENCE_PRESENT = get_evidence_present_types()

# Map common LLM variations to valid schema values
# This is kept here for backwards compatibility until normalizer is fully integrated
EVIDENCE_MAPPING = {
    # Logbook variations
    "service_book": "logbook",
    "service_logbook": "logbook",
    "log_book": "logbook",
    "service_history": "logbook",
    "full_service_history": "logbook",
    "fsh": "logbook",
    # Receipt variations
    "receipt": "receipts",
    "service_receipts": "receipts",
    "maintenance_receipts": "receipts",
    # Invoice variations
    "invoice": "workshop_invoice",
    "invoices": "workshop_invoice",
    "service_invoice": "workshop_invoice",
    "mechanic_invoice": "workshop_invoice",
    # Photo variations
    "photos": "photos_of_records",
    "photo": "photos_of_records",
    "pictures": "photos_of_records",
    "images": "photos_of_records",
    # None variations
    "no_records": "none",
    "no_evidence": "none",
    "unknown": "none",
}


def normalize_evidence_present(evidence_list: List[Any]) -> List[str]:
    """
    Normalize LLM evidence_present output to valid schema values.
    
    Handles:
    - Dicts vs strings
    - Common LLM variations (maps to valid values)
    - Invalid values (filtered out, not rejected)
    
    Args:
        evidence_list: Raw LLM output (may be strings or dicts)
        
    Returns:
        List of valid schema enum values only
    """
    if not evidence_list:
        return []
    
    normalized = set()
    
    for item in evidence_list:
        # Extract string value from dict if needed
        if isinstance(item, dict):
            value = str(item.get("type", item.get("value", ""))).lower().strip()
        elif isinstance(item, str):
            value = item.lower().strip()
        else:
            logger.debug(f"Skipping non-string/dict evidence item: {type(item)}")
            continue
        
        if not value:
            continue
        
        # Try direct match first
        if value in VALID_EVIDENCE_PRESENT:
            normalized.add(value)
        # Then try mapping
        elif value in EVIDENCE_MAPPING:
            normalized.add(EVIDENCE_MAPPING[value])
        else:
            # Log skipped values for monitoring
            logger.debug(f"Skipping invalid evidence_present value: {value}")
    
    return list(normalized)


def merge_signals(
    llm_signals: Dict[str, List[Dict[str, Any]]],
    rule_signals: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Merge LLM-extracted signals with rule-detected signals.
    
    Merge strategy:
    - Union both signal sets
    - Deduplicate by (type, evidence_text)
    - Prefer rule confidence for duplicates
    - Preserve verification levels
    
    Args:
        llm_signals: Signals from LLM extraction
        rule_signals: Signals from guardrail rules
        
    Returns:
        Merged signal dictionary
    """
    merged = {
        "legality": [],
        "accident_history": [],
        "mechanical_issues": [],
        "cosmetic_issues": [],
        "mods_performance": [],
        "mods_cosmetic": [],
        "seller_behavior": [],
    }
    
    for category in merged.keys():
        llm_list = llm_signals.get(category, [])
        rule_list = rule_signals.get(category, [])
        
        merged[category] = merge_signal_lists(llm_list, rule_list)
    
    return merged


def merge_signal_lists(
    llm_list: List[Dict[str, Any]],
    rule_list: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Merge two lists of signals with deduplication.
    
    Args:
        llm_list: Signals from LLM
        rule_list: Signals from rules
        
    Returns:
        Merged list with duplicates resolved
    """
    # Track signals by (type, normalized_evidence)
    signal_map: dict[tuple[str, str], dict[str, Any]] = {}
    
    # Add rule signals first (they have priority)
    for signal in rule_list:
        key = get_signal_key(signal)
        signal_map[key] = signal.copy()
        signal_map[key]["_source"] = "rule"
    
    # Add LLM signals, respecting rule priority
    for signal in llm_list:
        key = get_signal_key(signal)
        
        if key in signal_map:
            # Duplicate - merge, preferring rule confidence
            existing = signal_map[key]
            if existing.get("_source") == "rule":
                # Keep rule signal but merge any additional info from LLM
                continue
            else:
                # Both from LLM - keep higher confidence
                if signal.get("confidence", 0) > existing.get("confidence", 0):
                    signal_map[key] = signal.copy()
                    signal_map[key]["_source"] = "llm"
        else:
            # New signal from LLM
            signal_map[key] = signal.copy()
            signal_map[key]["_source"] = "llm"
    
    # Remove internal tracking field
    result = []
    for signal in signal_map.values():
        signal.pop("_source", None)
        result.append(signal)
    
    # Sort by confidence descending
    result.sort(key=lambda s: s.get("confidence", 0), reverse=True)
    
    return result


def get_signal_key(signal: Dict[str, Any]) -> Tuple[str, str]:
    """
    Generate a unique key for a signal for deduplication.
    
    Uses type and normalized evidence text.
    
    Args:
        signal: Signal dictionary
        
    Returns:
        Tuple key for deduplication
    """
    signal_type = signal.get("type", "unknown")
    evidence = signal.get("evidence_text", "")
    
    # Normalize evidence for comparison
    normalized_evidence = " ".join(evidence.lower().split())
    
    return (signal_type, normalized_evidence)


def merge_maintenance(
    llm_maintenance: Dict[str, Any],
    rule_signals: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Merge maintenance section.
    
    Rules don't directly detect maintenance claims, but we may
    add red flags based on detected signals.
    
    Args:
        llm_maintenance: Maintenance section from LLM
        rule_signals: Rule-detected signals (for context)
        
    Returns:
        Merged maintenance section with normalized and validated claims
    """
    # First, normalize the entire maintenance section using the normalizer
    # This handles invalid claim types, missing fields, and extra properties
    normalized = normalize_maintenance_via_normalizer(llm_maintenance)
    
    # Build result from normalized maintenance
    result = {
        "claims": normalized.get("claims", []),
        "evidence_present": normalized.get("evidence_present", []),
        "red_flags": normalized.get("red_flags", []),
    }
    
    # Deduplicate claims
    result["claims"] = deduplicate_claims(result["claims"])
    
    # Deduplicate red flags
    result["red_flags"] = deduplicate_red_flags(result["red_flags"])
    
    return result


def deduplicate_claims(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate maintenance claims by type and evidence.
    
    Args:
        claims: List of maintenance claims
        
    Returns:
        Deduplicated list
    """
    seen = set()
    result = []
    
    for claim in claims:
        key = (
            claim.get("type", ""),
            " ".join(claim.get("evidence_text", "").lower().split()),
        )
        if key not in seen:
            seen.add(key)
            result.append(claim)
    
    return result


def deduplicate_red_flags(red_flags: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicate maintenance red flags by type and evidence.
    
    Args:
        red_flags: List of red flags
        
    Returns:
        Deduplicated list
    """
    seen = set()
    result = []
    
    for flag in red_flags:
        key = (
            flag.get("type", ""),
            " ".join(flag.get("evidence_text", "").lower().split()),
        )
        if key not in seen:
            seen.add(key)
            result.append(flag)
    
    return result


def count_signals_by_severity(signals: Dict[str, List[Dict[str, Any]]]) -> Dict[str, int]:
    """
    Count signals by severity level.
    
    Args:
        signals: Signal dictionary
        
    Returns:
        Dictionary with counts per severity
    """
    counts = {"low": 0, "medium": 0, "high": 0}
    
    for signal_list in signals.values():
        for signal in signal_list:
            severity = signal.get("severity", "low")
            if severity in counts:
                counts[severity] += 1
    
    return counts


def get_highest_severity_signals(
    signals: Dict[str, List[Dict[str, Any]]],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """
    Get the highest severity signals across all categories.
    
    Args:
        signals: Signal dictionary
        limit: Maximum number to return
        
    Returns:
        List of highest severity signals
    """
    all_signals = []
    for category, signal_list in signals.items():
        for signal in signal_list:
            signal_with_category = signal.copy()
            signal_with_category["_category"] = category
            all_signals.append(signal_with_category)
    
    # Sort by severity (high > medium > low) then by confidence
    severity_order = {"high": 0, "medium": 1, "low": 2}
    all_signals.sort(
        key=lambda s: (
            severity_order.get(s.get("severity", "low"), 3),
            -s.get("confidence", 0),
        )
    )
    
    # Remove internal field and limit
    result = []
    for signal in all_signals[:limit]:
        signal.pop("_category", None)
        result.append(signal)
    
    return result
