"""
Flipability Score Calculator (MVP)

Estimates how easy it is to buy and resell a vehicle for profit with low risk.
Deterministic, explainable, and stable.
"""

from typing import Dict, List, Any, Optional, Tuple
import math

# --- Constants & Multipliers ---

# Verified Penalties
# Maps signal type to multiplier (0.0 - 1.0)
VERIFIED_PENALTIES = {
    # Accident / Title
    "writeoff": 0.25,
    "repairable_writeoff": 0.25,
    "salvage_title": 0.25,
    "rebuilt_title": 0.25,
    "wovr_listed": 0.25,
    "structural_damage": 0.30,
    "chassis_damage": 0.30,
    "flood_damage": 0.30,
    "airbag_deployed": 0.30,
    "accident_damage": 0.60,
    "hail_damage": 0.75,

    # Legality
    "defected": 0.35,
    "unregistered": 0.35,
    "no_rego": 0.35,
    "not_roadworthy": 0.35,
    "no_rwc": 0.60,
    "rego_expired": 0.70,
    "inspection_required": 0.80,

    # Mechanical
    "not_running": 0.45,
    "engine_knock": 0.45,
    "engine_overheating": 0.45,
    "gearbox_issue": 0.45,
    "slipping_transmission": 0.45,
    "head_gasket_suspected": 0.45,
    "oil_leak": 0.70,
    "coolant_leak": 0.70,
    "check_engine_light": 0.70,
    "needs_mechanic": 0.70,

    # Performance Mods
    "stage_2_or_higher": 0.60,
    "e85_flex_fuel": 0.60,
    "turbo_swap": 0.60,
    "engine_swap": 0.60,
    "race_build": 0.60,
    "track_use": 0.60,
    "tuned": 0.75,
    "ecu_tune": 0.75,
    "turbo_upgrade": 0.75,
}

# Service History Penalties
SERVICE_HISTORY_PENALTIES = {
    "none": 0.70,
    "partial": 0.85,
}

def calculate_value_advantage(asking_price: float, market_p50: float) -> int:
    """
    Computes Value Advantage Score (0-100) based on deal delta percentage.
    """
    if not asking_price or not market_p50 or market_p50 == 0:
        return 0

    deal_delta_pct = (market_p50 - asking_price) / market_p50

    if deal_delta_pct <= -0.05:
        return 10
    elif -0.05 < deal_delta_pct <= 0.00:
        return 20
    elif 0.00 < deal_delta_pct <= 0.05:
        return 40
    elif 0.05 < deal_delta_pct <= 0.10:
        return 60
    elif 0.10 < deal_delta_pct < 0.20:
        return 80
    else: # >= 0.20
        return 95

def calculate_liquidity_score(comps_used_count: int) -> int:
    """
    Computes Liquidity Proxy Score (0-100) based on comps count.
    """
    if comps_used_count >= 50:
        return 100
    elif 20 <= comps_used_count <= 49:
        return 80
    elif 10 <= comps_used_count <= 19:
        return 60
    elif 5 <= comps_used_count <= 9:
        return 45
    else: # < 5
        return 30

def calculate_risk_multiplier(
    signals: Dict[str, List[Dict[str, Any]]],
    service_history_level: str
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Computes Risk Multiplier (0.10-1.00) based on signals and service history.
    Returns the multiplier and a list of penalties applied.
    """
    candidate_multipliers = []
    penalties_applied = []

    # 1. Check Signal Penalties
    # Flatten all signals from all categories
    all_signals = []
    for category in signals.values():
        if isinstance(category, list):
            all_signals.extend(category)

    for signal in all_signals:
        signal_type = signal.get("type")
        verification_level = signal.get("verification_level", "inferred")
        
        if signal_type in VERIFIED_PENALTIES:
            base_multiplier = VERIFIED_PENALTIES[signal_type]
            
            if verification_level == "verified":
                multiplier = base_multiplier
            else:
                # Inferred softening: (1 + verified) / 2
                multiplier = (1.0 + base_multiplier) / 2.0
            
            candidate_multipliers.append(multiplier)
            penalties_applied.append({
                "type": signal_type,
                "severity": signal.get("severity"),
                "verification_level": verification_level,
                "multiplier": multiplier,
                "evidence_text": signal.get("evidence_text")
            })

    # 2. Check Service History Penalties
    if service_history_level in SERVICE_HISTORY_PENALTIES:
        multiplier = SERVICE_HISTORY_PENALTIES[service_history_level]
        candidate_multipliers.append(multiplier)
        penalties_applied.append({
            "type": f"service_history_{service_history_level}",
            "severity": "medium" if service_history_level == "partial" else "high",
            "verification_level": "verified", # Service history level is usually derived from aggregated signals
            "multiplier": multiplier,
            "evidence_text": f"Service history level is {service_history_level}"
        })

    # 3. Determine Final Multiplier
    if not candidate_multipliers:
        return 1.0, []
    
    # Min multiplier (most punishing)
    risk_multiplier = min(candidate_multipliers)
    
    # Clamp to [0.10, 1.00] (though logic above shouldn't exceed 1.0 or drop below 0.10 naturally if config is correct)
    risk_multiplier = max(0.10, min(1.0, risk_multiplier))

    return risk_multiplier, penalties_applied

def calculate_confidence(
    comps_used_count: int,
    risk_level_overall: str,
    extraction_warnings: List[str]
) -> float:
    """
    Computes Confidence (0-1) based on comps and data quality.
    """
    # Base confidence from comps
    if comps_used_count >= 50:
        confidence = 0.9
    elif 20 <= comps_used_count <= 49:
        confidence = 0.8
    elif 10 <= comps_used_count <= 19:
        confidence = 0.7
    elif 5 <= comps_used_count <= 9:
        confidence = 0.6
    else:
        confidence = 0.5

    # Penalties
    if risk_level_overall == "unknown":
        confidence -= 0.1
    
    for warning in extraction_warnings:
        if "description" in warning.lower() and ("short" in warning.lower() or "brief" in warning.lower()):
             confidence -= 0.1
             break # Apply once

    # Clamp
    return max(0.3, min(0.95, confidence))

def generate_dominant_factors(
    value_score: int,
    liquidity_score: int,
    penalties: List[Dict[str, Any]],
    deal_delta_pct: float,
    comps_count: int
) -> List[str]:
    """
    Generates explanation strings.
    """
    factors = []

    # Value Factor
    if value_score >= 80:
        factors.append(f"Strong Value: Asking price is {abs(deal_delta_pct)*100:.1f}% below estimated market median")
    elif value_score <= 20:
        factors.append(f"Poor Value: Asking price is {abs(deal_delta_pct)*100:.1f}% above estimated market median")

    # Liquidity Factor
    if liquidity_score >= 80:
        factors.append(f"High Liquidity: Strong comps coverage ({comps_count} similar listings found)")
    elif liquidity_score <= 45:
        factors.append(f"Low Liquidity: Thin comps pool ({comps_count} similar listings found)")

    # Penalty Factors
    if penalties:
        # Sort by multiplier ascending (most severe first)
        sorted_penalties = sorted(penalties, key=lambda x: x['multiplier'])
        top_penalty = sorted_penalties[0]
        factors.append(f"Risk Penalty: {top_penalty['type'].replace('_', ' ').title()} reduces flipability (x{top_penalty['multiplier']:.2f})")
        
        if len(penalties) > 1:
            factors.append(f"Multiple risks detected ({len(penalties)} total)")

    return factors

def calculate_flipability(
    stage7_payload: Dict[str, Any],
    stage4_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main entry point to calculate Flipability Score.
    """
    # 1. Extract Inputs
    asking_price = stage7_payload.get("asking_price")
    market_p50 = stage7_payload.get("estimated_market_price_p50")
    comps_used_count = stage7_payload.get("comps_used_count", 0)
    
    risk_level_overall = stage4_payload.get("risk_level_overall", "unknown")
    signals = stage4_payload.get("signals", {})
    service_history_level = stage4_payload.get("service_history_level", "unknown")
    extraction_warnings = stage4_payload.get("extraction_warnings", [])

    # 2. Compute Components
    value_score = calculate_value_advantage(asking_price, market_p50)
    liquidity_score = calculate_liquidity_score(comps_used_count)
    risk_multiplier, penalties = calculate_risk_multiplier(signals, service_history_level)
    
    # 3. Compute Final Score
    base_score = (0.55 * value_score) + (0.45 * liquidity_score)
    final_score = round(base_score * risk_multiplier)
    final_score = max(0, min(100, final_score))

    # 4. Compute Confidence
    confidence = calculate_confidence(comps_used_count, risk_level_overall, extraction_warnings)

    # 5. Generate Explanations
    deal_delta_pct = 0.0
    if asking_price and market_p50:
        deal_delta_pct = (market_p50 - asking_price) / market_p50
        
    dominant_factors = generate_dominant_factors(
        value_score, 
        liquidity_score, 
        penalties, 
        deal_delta_pct, 
        comps_used_count
    )

    # 6. Construct Payload
    return {
        "flipability_score": int(final_score),
        "components": {
            "value_advantage_score": int(value_score),
            "liquidity_score": int(liquidity_score),
            "risk_multiplier": float(risk_multiplier),
            "confidence": float(confidence)
        },
        "dominant_factors": dominant_factors,
        "penalties_applied": penalties,
        "inputs_used": {
            "asking_price": asking_price,
            "market_p50": market_p50,
            "comps_used_count": comps_used_count,
            "risk_level_overall": risk_level_overall
        }
    }
