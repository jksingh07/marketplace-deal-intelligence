"""
Guardrail Rules Module for Stage 4

Implements deterministic rule-based detection for high-severity signals.
These rules act as a safety net to ensure critical signals are never missed.

Rules:
- Only ADD signals (never remove)
- Always produce verification_level=verified
- Always include evidence_text as exact substring
- Always set high confidence (0.90-1.00)
"""

import re
from typing import Any, Dict, List, Set

from config import GUARDRAIL_DEFAULT_CONFIDENCE
from stage4.text_prep import PreparedText, find_evidence_span


# ============================================================================
# Rule Definitions
# ============================================================================

# Each rule is a tuple of:
# (pattern, signal_type, signal_category, severity)

WRITEOFF_SALVAGE_RULES = [
    (r'\bwrite[\s-]?off\b', 'writeoff', 'accident_history', 'high'),
    (r'\bwritten[\s-]?off\b', 'writeoff', 'accident_history', 'high'),
    (r'\brepairable[\s-]?write[\s-]?off\b', 'repairable_writeoff', 'accident_history', 'high'),
    (r'\bsalvage\s*title\b', 'salvage_title', 'accident_history', 'high'),
    (r'\bsalvage\s*vehicle\b', 'salvage_title', 'accident_history', 'high'),
    (r'\bsalvage\b', 'salvage_title', 'accident_history', 'high'),
    (r'\brebuilt\s*title\b', 'rebuilt_title', 'accident_history', 'high'),
    (r'\bwovr\b', 'wovr_listed', 'accident_history', 'high'),
    (r'\bflood(?:ed)?\s*damage[d]?\b', 'flood_damage', 'accident_history', 'high'),
    (r'\bwater\s*damage[d]?\b', 'flood_damage', 'accident_history', 'high'),
    (r'\bstructural\s*damage\b', 'structural_damage', 'accident_history', 'high'),
    (r'\bframe\s*damage\b', 'structural_damage', 'accident_history', 'high'),
    (r'\bchassis\s*damage\b', 'chassis_damage', 'accident_history', 'high'),
    (r'\bairbag[s]?\s*deployed\b', 'airbag_deployed', 'accident_history', 'high'),
]

LEGALITY_RULES = [
    (r'\bdefect(?:ed)?\b', 'defected', 'legality', 'high'),
    (r'\bunregistered\b', 'unregistered', 'legality', 'high'),
    (r'\bunreg\b', 'unregistered', 'legality', 'high'),
    (r'\bno\s*rego\b', 'no_rego', 'legality', 'high'),
    (r'\brego\s*expired\b', 'rego_expired', 'legality', 'high'),
    (r'\bno\s*rwc\b', 'no_rwc', 'legality', 'high'),
    (r'\bwithout\s*rwc\b', 'no_rwc', 'legality', 'high'),
    (r'\bneeds?\s*rwc\b', 'rwc_required', 'legality', 'medium'),
    (r'\brwc\s*required\b', 'rwc_required', 'legality', 'medium'),
    (r'\bnot\s*roadworthy\b', 'not_roadworthy', 'legality', 'high'),
    (r'\binspection\s*required\b', 'inspection_required', 'legality', 'medium'),
    (r'\bblue\s*slip\b', 'inspection_required', 'legality', 'medium'),
    (r'\bpink\s*slip\b', 'inspection_required', 'legality', 'medium'),
]

MECHANICAL_RULES = [
    (r'\bnot\s*running\b', 'not_running', 'mechanical_issues', 'high'),
    (r'\bwon\'?t\s*start\b', 'not_running', 'mechanical_issues', 'high'),
    (r'\bdoesn\'?t\s*start\b', 'starting_issue', 'mechanical_issues', 'high'),
    (r'\bengine\s*blown\b', 'not_running', 'mechanical_issues', 'high'),
    (r'\bblown\s*engine\b', 'not_running', 'mechanical_issues', 'high'),
    (r'\bengine\s*knock(?:ing)?\b', 'engine_knock', 'mechanical_issues', 'high'),
    (r'\bknocking\b', 'engine_knock', 'mechanical_issues', 'high'),
    (r'\boverheating\b', 'engine_overheating', 'mechanical_issues', 'high'),
    (r'\bover\s*heats?\b', 'engine_overheating', 'mechanical_issues', 'high'),
    (r'\bruns?\s*hot\b', 'engine_overheating', 'mechanical_issues', 'high'),
    (r'\bgearbox\s*(?:issue|problem|fault)\b', 'gearbox_issue', 'mechanical_issues', 'high'),
    (r'\btransmission\s*(?:issue|problem|fault)\b', 'gearbox_issue', 'mechanical_issues', 'high'),
    (r'\bslipping\b', 'slipping_transmission', 'mechanical_issues', 'high'),
    (r'\bslips\b', 'slipping_transmission', 'mechanical_issues', 'high'),
    (r'\bhead\s*gasket\b', 'head_gasket_suspected', 'mechanical_issues', 'high'),
]

PERFORMANCE_MODS_RULES = [
    (r'\btuned\b', 'tuned', 'mods_performance', 'medium'),
    (r'\btune\b', 'tuned', 'mods_performance', 'medium'),
    (r'\becu\s*tune[d]?\b', 'ecu_tune', 'mods_performance', 'medium'),
    (r'\bremapped\b', 'ecu_tune', 'mods_performance', 'medium'),
    (r'\bstage\s*2\b', 'stage_2_or_higher', 'mods_performance', 'high'),
    (r'\bstage2\b', 'stage_2_or_higher', 'mods_performance', 'high'),
    (r'\bstage\s*3\b', 'stage_2_or_higher', 'mods_performance', 'high'),
    (r'\bstage3\b', 'stage_2_or_higher', 'mods_performance', 'high'),
    (r'\be85\b', 'e85_flex_fuel', 'mods_performance', 'high'),
    (r'\bflex\s*fuel\b', 'e85_flex_fuel', 'mods_performance', 'high'),
    (r'\btrack\s*car\b', 'track_use', 'mods_performance', 'high'),
    (r'\btrack\s*use\b', 'track_use', 'mods_performance', 'high'),
    (r'\brace\s*build\b', 'race_build', 'mods_performance', 'high'),
    (r'\bturbo\s*swap\b', 'turbo_swap', 'mods_performance', 'high'),
    (r'\bturbo\s*upgrade\b', 'turbo_upgrade', 'mods_performance', 'high'),
    (r'\bsupercharger\b', 'supercharger', 'mods_performance', 'high'),
    (r'\bengine\s*swap\b', 'engine_swap', 'mods_performance', 'high'),
]

SELLER_BEHAVIOR_RULES = [
    (r'\bfirm\s*price\b', 'firm_price', 'seller_behavior', 'medium'),
    (r'\bprice\s*is\s*firm\b', 'firm_price', 'seller_behavior', 'medium'),
    (r'\bfixed\s*price\b', 'firm_price', 'seller_behavior', 'medium'),
    (r'\bno\s*low\s*ballers?\b', 'no_lowballers', 'seller_behavior', 'low'),
    (r'\bno\s*lowballers?\b', 'no_lowballers', 'seller_behavior', 'low'),
    (r'\bno\s*time\s*wasters?\b', 'no_timewasters', 'seller_behavior', 'low'),
    (r'\bno\s*timewasters?\b', 'no_timewasters', 'seller_behavior', 'low'),
    (r'\bneed\s*gone\b', 'need_gone', 'seller_behavior', 'medium'),
    (r'\bmust\s*sell\b', 'urgent_sale', 'seller_behavior', 'medium'),
    (r'\burgent\s*sale\b', 'urgent_sale', 'seller_behavior', 'medium'),
    (r'\bswap[s]?\b', 'swap_trade', 'seller_behavior', 'low'),
    (r'\btrade[s]?\s*(?:in|welcome)?\b', 'swap_trade', 'seller_behavior', 'low'),
]

ALL_RULES = (
    WRITEOFF_SALVAGE_RULES +
    LEGALITY_RULES +
    MECHANICAL_RULES +
    PERFORMANCE_MODS_RULES +
    SELLER_BEHAVIOR_RULES
)


# ============================================================================
# Main Guardrail Functions
# ============================================================================

def run_guardrails(prepared_text: PreparedText) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run all guardrail rules against the prepared text.
    
    Args:
        prepared_text: PreparedText object with original and normalized text
        
    Returns:
        Dictionary of signal category -> list of detected signals
    """
    signals = {
        "legality": [],
        "accident_history": [],
        "mechanical_issues": [],
        "cosmetic_issues": [],
        "mods_performance": [],
        "mods_cosmetic": [],
        "seller_behavior": [],
    }
    
    # Track what we've already detected to avoid duplicates
    detected = set()
    
    for pattern, signal_type, category, severity in ALL_RULES:
        # Search in normalized (lowercase) text
        matches = list(re.finditer(pattern, prepared_text.normalized_text, re.IGNORECASE))
        
        for match in matches:
            # Create unique key for deduplication
            key = (category, signal_type, match.group().lower())
            if key in detected:
                continue
            detected.add(key)
            
            # Find evidence span in original text
            evidence = find_evidence_span(
                match.group(),
                prepared_text.combined_text,
                prepared_text.sentences,
            )
            
            if not evidence:
                # Fallback to the match itself if we can't find context
                evidence = match.group()
            
            # Create signal
            signal = {
                "type": signal_type,
                "severity": severity,
                "verification_level": "verified",
                "evidence_text": evidence,
                "confidence": GUARDRAIL_DEFAULT_CONFIDENCE,
            }
            
            signals[category].append(signal)
    
    return signals


def check_high_risk_keywords(text: str) -> bool:
    """
    Quick check if text contains any high-risk keywords.
    
    Useful for the source_text_stats field.
    
    Args:
        text: Text to check
        
    Returns:
        True if any high-risk keyword found
    """
    text_lower = text.lower()
    
    high_risk_patterns = [
        r'\bwrite[\s-]?off\b',
        r'\bdefect(?:ed)?\b',
        r'\bnot\s*running\b',
        r'\bsalvage\b',
        r'\bflood\b',
        r'\bstructural\s*damage\b',
        r'\bstage\s*[23]\b',
        r'\be85\b',
        r'\btrack\s*(?:car|use)\b',
    ]
    
    for pattern in high_risk_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False


def get_guardrail_categories() -> List[str]:
    """Get list of signal categories covered by guardrails."""
    return [
        "legality",
        "accident_history",
        "mechanical_issues",
        "mods_performance",
        "seller_behavior",
    ]


def get_high_severity_types() -> Set[str]:
    """Get set of signal types that are high severity."""
    return {
        signal_type
        for _, signal_type, _, severity in ALL_RULES
        if severity == "high"
    }
