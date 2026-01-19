"""
Derived Fields Module for Stage 4

Computes deterministic summary fields from extracted signals.
These computations are NOT done by the LLM - they are rule-based.
"""

from typing import Any, Dict, List


def compute_derived_fields(
    signals: Dict[str, List[Dict[str, Any]]],
    maintenance: Dict[str, Any],
    llm_summaries: Dict[str, str],
) -> Dict[str, str]:
    """
    Compute all derived summary fields.
    
    Args:
        signals: Merged signals dictionary
        maintenance: Maintenance section
        llm_summaries: LLM-provided summaries (used as hints, not authority)
        
    Returns:
        Dictionary of computed summary fields
    """
    return {
        "risk_level_overall": compute_risk_level_overall(signals),
        "mods_risk_level": compute_mods_risk_level(signals.get("mods_performance", [])),
        "service_history_level": compute_service_history_level(maintenance),
        "negotiation_stance": compute_negotiation_stance(signals.get("seller_behavior", [])),
        "claimed_condition": compute_claimed_condition(signals, llm_summaries),
    }


def compute_risk_level_overall(signals: Dict[str, List[Dict[str, Any]]]) -> str:
    """
    Compute overall risk level based on all signals.
    
    Rules:
    - HIGH: Any HIGH severity verified signal exists
    - MEDIUM: Multiple medium signals OR any medium verified + missing evidence
    - LOW: Only low cosmetic signals and no major red flags
    - UNKNOWN: Insufficient information
    
    Args:
        signals: All signals dictionary
        
    Returns:
        Risk level enum value
    """
    high_verified_count = 0
    high_inferred_count = 0
    medium_verified_count = 0
    medium_inferred_count = 0
    low_count = 0
    total_count = 0
    
    # High-impact categories (not cosmetic)
    high_impact_categories = [
        "legality",
        "accident_history",
        "mechanical_issues",
        "mods_performance",
    ]
    
    for category, signal_list in signals.items():
        for signal in signal_list:
            total_count += 1
            severity = signal.get("severity", "low")
            verification = signal.get("verification_level", "inferred")
            
            # Only count high-impact categories for risk
            if category in high_impact_categories:
                if severity == "high":
                    if verification == "verified":
                        high_verified_count += 1
                    else:
                        high_inferred_count += 1
                elif severity == "medium":
                    if verification == "verified":
                        medium_verified_count += 1
                    else:
                        medium_inferred_count += 1
                else:
                    low_count += 1
    
    # Decision logic
    if high_verified_count > 0:
        return "high"
    
    if high_inferred_count >= 2 or (high_inferred_count >= 1 and medium_verified_count >= 1):
        return "high"
    
    if medium_verified_count >= 2 or (medium_verified_count >= 1 and medium_inferred_count >= 2):
        return "medium"
    
    if high_inferred_count >= 1 or medium_verified_count >= 1:
        return "medium"
    
    if total_count == 0:
        return "unknown"
    
    return "low"


def compute_mods_risk_level(mods_performance: List[Dict[str, Any]]) -> str:
    """
    Compute modification risk level.
    
    Rules:
    - NONE: No performance mods
    - LOW: Cosmetic mods only (handled elsewhere)
    - MEDIUM: Intake/exhaust, mild tune, suspension
    - HIGH: Stage 2+, turbo swap, E85, track/race, engine swap
    - UNKNOWN: Unclear
    
    Args:
        mods_performance: Performance modification signals
        
    Returns:
        Mods risk level enum value
    """
    if not mods_performance:
        return "none"
    
    # High risk mod types
    high_risk_types = {
        "stage_2_or_higher",
        "turbo_swap",
        "turbo_upgrade",
        "supercharger",
        "engine_swap",
        "e85_flex_fuel",
        "track_use",
        "race_build",
        "fuel_system_upgrade",
    }
    
    # Medium risk mod types
    medium_risk_types = {
        "tuned",
        "ecu_tune",
        "stage_1",
        "intake_exhaust",
        "downpipe",
        "intercooler_upgrade",
    }
    
    has_high = False
    has_medium = False
    
    for mod in mods_performance:
        mod_type = mod.get("type", "")
        if mod_type in high_risk_types:
            has_high = True
        elif mod_type in medium_risk_types:
            has_medium = True
    
    if has_high:
        return "high"
    if has_medium:
        return "medium"
    
    return "low"


def compute_service_history_level(maintenance: Dict[str, Any]) -> str:
    """
    Compute service history level from maintenance section.
    
    Rules:
    - FULL: Explicit "full service history", logbook + receipts
    - PARTIAL: "some receipts", "serviced regularly" without proof
    - NONE: Explicit "no service history", "no logbooks"
    - UNKNOWN: Not mentioned
    
    Args:
        maintenance: Maintenance section from extraction
        
    Returns:
        Service history level enum value
    """
    claims = maintenance.get("claims", [])
    evidence_present = maintenance.get("evidence_present", [])
    
    # Check evidence types
    has_logbook = "logbook" in evidence_present
    has_receipts = "receipts" in evidence_present or "workshop_invoice" in evidence_present
    
    # Check claim types
    claim_types = {c.get("type", "") for c in claims}
    
    has_full_history = "logbook_mentioned" in claim_types or has_logbook
    has_receipts_mentioned = "receipts_mentioned" in claim_types or has_receipts
    has_regular_service = "regular_service_claimed" in claim_types
    has_recent_service = "serviced_recently" in claim_types
    
    # Decision logic
    if has_full_history and (has_receipts_mentioned or has_receipts):
        return "full"
    
    if has_full_history:
        return "full"
    
    if has_receipts_mentioned or has_regular_service or has_recent_service:
        return "partial"
    
    # Check for explicit "none" indicators
    if "none" in evidence_present and not claims:
        return "none"
    
    if not claims and not evidence_present:
        return "unknown"
    
    return "partial"


def compute_negotiation_stance(seller_behavior: List[Dict[str, Any]]) -> str:
    """
    Compute negotiation stance from seller behavior signals.
    
    Rules:
    - FIRM: "firm price", "no lowballers", "price is fixed"
    - OPEN: "open to offers", "negotiable"
    - UNKNOWN: Not mentioned
    
    Args:
        seller_behavior: Seller behavior signals
        
    Returns:
        Negotiation stance enum value
    """
    if not seller_behavior:
        return "unknown"
    
    # Extract types
    types = {s.get("type", "") for s in seller_behavior}
    
    # Firm indicators
    firm_types = {"firm_price", "no_lowballers", "no_timewasters"}
    
    # Open indicators
    open_types = {"open_to_offers", "need_gone", "urgent_sale", "moving_sale"}
    
    has_firm = bool(types & firm_types)
    has_open = bool(types & open_types)
    
    # Urgency signals suggest flexibility
    if has_open and not has_firm:
        return "open"
    
    if has_firm and not has_open:
        return "firm"
    
    # Both present - urgency usually wins
    if has_open and has_firm:
        # Check for strong urgency
        strong_urgency = {"need_gone", "urgent_sale"}
        if types & strong_urgency:
            return "open"
        return "firm"
    
    return "unknown"


def compute_claimed_condition(
    signals: Dict[str, List[Dict[str, Any]]],
    llm_summaries: Dict[str, str],
) -> str:
    """
    Compute claimed condition based on signals and LLM hint.
    
    Rules:
    - EXCELLENT: "immaculate", "like new", "perfect"
    - GOOD: "good condition", "well maintained"
    - FAIR: "average", "some wear", "minor issues"
    - NEEDS_WORK: "needs work", "project", "mechanic special", "not running"
    - UNKNOWN: If none stated
    
    Args:
        signals: All signals
        llm_summaries: LLM-provided summaries including claimed_condition
        
    Returns:
        Claimed condition enum value
    """
    # First check if we have explicit not_running
    mechanical = signals.get("mechanical_issues", [])
    for issue in mechanical:
        if issue.get("type") == "not_running":
            return "needs_work"
    
    # Check for high severity issues that indicate needs_work
    high_severity_count = 0
    for category in ["mechanical_issues", "legality", "accident_history"]:
        for signal in signals.get(category, []):
            if signal.get("severity") == "high" and signal.get("verification_level") == "verified":
                high_severity_count += 1
    
    if high_severity_count >= 2:
        return "needs_work"
    
    # Use LLM hint if available and reasonable
    llm_condition = llm_summaries.get("claimed_condition", "unknown")
    
    # Validate LLM condition against signals
    if llm_condition == "excellent" and high_severity_count > 0:
        return "fair"  # Downgrade if issues found
    
    if llm_condition in ["excellent", "good", "fair", "needs_work"]:
        return llm_condition
    
    # Infer from signals
    if high_severity_count >= 1:
        return "fair"
    
    return "unknown"


def compute_missing_info(
    signals: Dict[str, List[Dict[str, Any]]],
    maintenance: Dict[str, Any],
    text_stats: Dict[str, Any],
) -> List[str]:
    """
    Compute what critical information is missing.
    
    Args:
        signals: All signals
        maintenance: Maintenance section
        text_stats: Source text statistics
        
    Returns:
        List of missing_info enum values
    """
    missing = []
    
    # Check service history
    claims = maintenance.get("claims", [])
    evidence = maintenance.get("evidence_present", [])
    if not claims and "none" not in evidence:
        missing.append("service_history_unknown")
    
    # Always flag these as potentially unknown unless explicitly mentioned
    # (The LLM should have populated these if mentioned)
    default_missing = [
        "accident_history_unknown",
        "rego_expiry_unknown",
        "rwc_status_unknown",
        "number_of_owners_unknown",
    ]
    
    # Check legality signals - if we found explicit info, don't mark as unknown
    legality_types = {s.get("type") for s in signals.get("legality", [])}
    if not legality_types:
        missing.extend(["rego_expiry_unknown", "rwc_status_unknown"])
    
    # Check accident history
    accident_types = {s.get("type") for s in signals.get("accident_history", [])}
    if not accident_types:
        missing.append("accident_history_unknown")
    
    # Deduplicate
    return list(set(missing))
