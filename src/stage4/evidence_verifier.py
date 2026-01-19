"""
Evidence Verification Module for Stage 4

Validates that all extracted signals have verbatim evidence in the source text.
This is critical for preventing hallucinations.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

from config import VERIFIED_MIN_CONFIDENCE, INFERRED_MIN_CONFIDENCE
from stage4.text_prep import check_evidence_exists
from common.schema_enums import get_all_signal_types, is_valid_signal_type

# Configure logging
logger = logging.getLogger(__name__)


def verify_signals(
    extraction_result: Dict[str, Any],
    original_text: str,
) -> Dict[str, Any]:
    """
    Verify all signals in the extraction result have valid evidence.
    
    Signals are classified as:
    - verified: evidence_text found verbatim, high confidence
    - inferred: evidence_text found, indirect wording
    - rejected: evidence_text not found (removed from output)
    
    Args:
        extraction_result: Raw LLM extraction output
        original_text: Original title + description text
        
    Returns:
        Extraction result with verified signals only
    """
    if "payload" not in extraction_result:
        return extraction_result
    
    payload = extraction_result["payload"]
    
    # Verify signal arrays
    if "signals" in payload:
        signals = payload["signals"]
        
        signals["legality"] = verify_signal_list(
            signals.get("legality", []), original_text, category="legality"
        )
        signals["accident_history"] = verify_signal_list(
            signals.get("accident_history", []), original_text, category="accident_history"
        )
        signals["mechanical_issues"] = verify_signal_list(
            signals.get("mechanical_issues", []), original_text, category="mechanical_issues"
        )
        signals["cosmetic_issues"] = verify_signal_list(
            signals.get("cosmetic_issues", []), original_text, category="cosmetic_issues"
        )
        signals["mods_performance"] = verify_signal_list(
            signals.get("mods_performance", []), original_text, category="mods_performance"
        )
        signals["mods_cosmetic"] = verify_signal_list(
            signals.get("mods_cosmetic", []), original_text, category="mods_cosmetic"
        )
        signals["seller_behavior"] = verify_signal_list(
            signals.get("seller_behavior", []), original_text, category="seller_behavior"
        )
    
    # Verify maintenance claims
    if "maintenance" in payload:
        maintenance = payload["maintenance"]
        maintenance["claims"] = verify_maintenance_claims(
            maintenance.get("claims", []), original_text
        )
        maintenance["red_flags"] = verify_signal_list(
            maintenance.get("red_flags", []), original_text
        )
    
    return extraction_result


def verify_signal_list(
    signals: List[Dict[str, Any]],
    original_text: str,
    category: str = None,
) -> List[Dict[str, Any]]:
    """
    Verify a list of signals, rejecting those without valid evidence or invalid types.
    
    Args:
        signals: List of signal dictionaries
        original_text: Original text to check against
        category: Signal category name for type validation
        
    Returns:
        List of verified signals only
    """
    verified_signals = []
    
    for signal in signals:
        verified_signal = verify_single_signal(signal, original_text, category=category)
        if verified_signal is not None:
            verified_signals.append(verified_signal)
    
    return verified_signals


# Signal types are now loaded from schema via common.schema_enums
# This eliminates duplication and ensures consistency


def verify_signal_type(signal: Dict[str, Any], category: str) -> bool:
    """
    Check if signal type is valid for the given category.
    
    Uses centralized enum definitions from schema_enums.
    
    Args:
        signal: Signal dictionary with 'type' field
        category: Signal category name
        
    Returns:
        True if type is valid for category, False otherwise
    """
    signal_type = signal.get("type", "")
    is_valid = is_valid_signal_type(signal_type, category)
    
    if not is_valid:
        logger.debug(f"Invalid signal type '{signal_type}' for category '{category}'")
    
    return is_valid


def verify_single_signal(
    signal: Dict[str, Any],
    original_text: str,
    category: str = None,
) -> Optional[Dict[str, Any]]:
    """
    Verify a single signal has valid evidence and type.
    
    Args:
        signal: Signal dictionary with evidence_text
        original_text: Original text to check against
        category: Optional category name for type validation
        
    Returns:
        Verified signal or None if rejected
    """
    # Validate signal type if category provided
    if category and not verify_signal_type(signal, category):
        # Invalid type - reject
        return None
    
    evidence_text = signal.get("evidence_text", "")
    
    if not evidence_text:
        # No evidence provided - reject
        return None
    
    # Check if evidence exists in original text
    if not check_evidence_exists(evidence_text, original_text):
        # Evidence not found - reject
        return None
    
    # Evidence found - classify verification level
    verification_level = signal.get("verification_level", "inferred")
    confidence = signal.get("confidence", 0.5)
    
    # Adjust confidence based on verification
    if verification_level == "verified":
        # Ensure confidence is appropriate for verified
        confidence = max(confidence, VERIFIED_MIN_CONFIDENCE)
    else:
        # Ensure confidence doesn't exceed verified threshold for inferred
        confidence = min(confidence, VERIFIED_MIN_CONFIDENCE - 0.05)
        confidence = max(confidence, INFERRED_MIN_CONFIDENCE)
    
    # Update signal
    signal["confidence"] = round(confidence, 2)
    signal["verification_level"] = verification_level
    
    return signal


def verify_maintenance_claims(
    claims: List[Dict[str, Any]],
    original_text: str,
) -> List[Dict[str, Any]]:
    """
    Verify maintenance claims have valid evidence.
    
    Args:
        claims: List of maintenance claim dictionaries
        original_text: Original text to check against
        
    Returns:
        List of verified claims only
    """
    verified_claims = []
    
    for claim in claims:
        evidence_text = claim.get("evidence_text", "")
        
        if not evidence_text:
            continue
            
        if not check_evidence_exists(evidence_text, original_text):
            continue
        
        # Evidence valid - keep claim
        verified_claims.append(claim)
    
    return verified_claims


def is_explicit_evidence(evidence_text: str, signal_type: str) -> bool:
    """
    Determine if evidence is explicit (verified) or implicit (inferred).
    
    Explicit evidence contains clear, unambiguous statements.
    Implicit evidence contains soft language or implications.
    
    Args:
        evidence_text: The evidence text
        signal_type: Type of signal being verified
        
    Returns:
        True if evidence is explicit, False if implicit
    """
    evidence_lower = evidence_text.lower()
    
    # Explicit indicators - clear, definitive language
    explicit_patterns = [
        r'\bwrite[\s-]?off\b',
        r'\bwritten[\s-]?off\b',
        r'\bdefected\b',
        r'\bunregistered\b',
        r'\bno rego\b',
        r'\bno rwc\b',
        r'\bnot running\b',
        r'\bwon\'?t start\b',
        r'\bengine blown\b',
        r'\bhead gasket\b',
        r'\bflood(?:ed)?\s+damage\b',
        r'\bsalvage\b',
        r'\btuned\b',
        r'\bstage\s*[23]\b',
        r'\be85\b',
        r'\btrack\s*(?:car|use|build)\b',
    ]
    
    for pattern in explicit_patterns:
        if re.search(pattern, evidence_lower):
            return True
    
    # Implicit indicators - soft language
    implicit_phrases = [
        "needs love",
        "bit of love",
        "needs work",
        "easy fix",
        "minor issue",
        "small problem",
        "could be",
        "might need",
        "may need",
        "not sure",
        "possibly",
        "seems to",
    ]
    
    for phrase in implicit_phrases:
        if phrase in evidence_lower:
            return False
    
    # Default to verified if evidence is present and no soft language
    return True


def classify_verification_level(
    evidence_text: str,
    signal_type: str,
    original_confidence: float,
) -> Tuple[str, float]:
    """
    Classify verification level and adjust confidence.
    
    Args:
        evidence_text: The evidence text
        signal_type: Type of signal
        original_confidence: Original confidence from LLM
        
    Returns:
        Tuple of (verification_level, adjusted_confidence)
    """
    if is_explicit_evidence(evidence_text, signal_type):
        # Verified - boost confidence
        confidence = max(original_confidence, VERIFIED_MIN_CONFIDENCE)
        return ("verified", round(confidence, 2))
    else:
        # Inferred - cap confidence
        confidence = min(original_confidence, VERIFIED_MIN_CONFIDENCE - 0.05)
        confidence = max(confidence, INFERRED_MIN_CONFIDENCE)
        return ("inferred", round(confidence, 2))


def count_verified_vs_inferred(signals: Dict[str, list]) -> Dict[str, int]:
    """
    Count verified vs inferred signals for stats.
    
    Args:
        signals: Signals dictionary from payload
        
    Returns:
        Dictionary with counts
    """
    verified_count = 0
    inferred_count = 0
    
    for signal_list in signals.values():
        if not isinstance(signal_list, list):
            continue
        for signal in signal_list:
            if signal.get("verification_level") == "verified":
                verified_count += 1
            else:
                inferred_count += 1
    
    return {
        "verified": verified_count,
        "inferred": inferred_count,
        "total": verified_count + inferred_count,
    }
