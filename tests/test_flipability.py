"""
Tests for Flipability Score Calculator
"""

import pytest
from src.common.scoring.flipability import calculate_flipability

def test_flipability_high_score():
    """
    Test Case 1: No risks, great undervaluation, high comps -> score should be high (80+)
    """
    stage7 = {
        "asking_price": 20000,
        "estimated_market_price_p50": 25000, # 20% undervaluation -> score 80-95
        "comps_used_count": 60 # > 50 -> liquidity 100
    }
    stage4 = {
        "risk_level_overall": "low",
        "signals": {},
        "service_history_level": "full",
        "extraction_warnings": []
    }

    result = calculate_flipability(stage7, stage4)
    
    score = result["flipability_score"]
    components = result["components"]
    
    # Value score should be 80 (0.10 < delta <= 0.20) or 95 if exactly 0.20
    # Delta = (25000 - 20000) / 25000 = 5000 / 25000 = 0.20 -> Score 95
    assert components["value_advantage_score"] == 95
    assert components["liquidity_score"] == 100
    assert components["risk_multiplier"] == 1.0
    
    # Base = 0.55 * 95 + 0.45 * 100 = 52.25 + 45 = 97.25
    # Final = 97 * 1.0 = 97
    assert score >= 80
    assert score == 97
    assert components["confidence"] == 0.9

def test_flipability_writeoff_verified():
    """
    Test Case 2: Writeoff verified -> risk multiplier 0.25 -> score should drop heavily
    """
    stage7 = {
        "asking_price": 20000,
        "estimated_market_price_p50": 25000, # Value 95
        "comps_used_count": 60 # Liquidity 100
    }
    stage4 = {
        "risk_level_overall": "high",
        "signals": {
            "accident_history": [
                {
                    "type": "writeoff",
                    "severity": "high",
                    "verification_level": "verified",
                    "evidence_text": "Statutory Writeoff"
                }
            ]
        },
        "service_history_level": "full",
        "extraction_warnings": []
    }

    result = calculate_flipability(stage7, stage4)
    
    components = result["components"]
    
    assert components["risk_multiplier"] == 0.25
    
    # Base = 97.25
    # Final = 97.25 * 0.25 = 24.31 -> 24
    assert result["flipability_score"] == 24
    assert len(result["penalties_applied"]) == 1
    assert result["penalties_applied"][0]["type"] == "writeoff"

def test_flipability_defected_inferred():
    """
    Test Case 3: Defected inferred -> softened multiplier applied
    """
    stage7 = {
        "asking_price": 20000,
        "estimated_market_price_p50": 20000, # Delta 0 -> Value 20
        "comps_used_count": 60 # Liquidity 100
    }
    stage4 = {
        "risk_level_overall": "medium",
        "signals": {
            "legality": [
                {
                    "type": "defected",
                    "severity": "high",
                    "verification_level": "inferred",
                    "evidence_text": "might have a defect"
                }
            ]
        },
        "service_history_level": "full",
        "extraction_warnings": []
    }

    result = calculate_flipability(stage7, stage4)
    
    components = result["components"]
    
    # Defected verified is 0.35
    # Inferred = (1 + 0.35) / 2 = 0.675
    assert components["risk_multiplier"] == 0.675
    
    # Base = 0.55 * 20 + 0.45 * 100 = 11 + 45 = 56
    # Final = 56 * 0.675 = 37.8 -> 38
    assert result["flipability_score"] == 38

def test_flipability_low_liquidity():
    """
    Test Case 4: Comps used count low (<5) -> low liquidity and low confidence
    """
    stage7 = {
        "asking_price": 20000,
        "estimated_market_price_p50": 20000,
        "comps_used_count": 3 # Liquidity 30
    }
    stage4 = {
        "risk_level_overall": "low",
        "signals": {},
        "service_history_level": "full",
        "extraction_warnings": []
    }

    result = calculate_flipability(stage7, stage4)
    
    components = result["components"]
    
    assert components["liquidity_score"] == 30
    assert components["confidence"] == 0.5

def test_flipability_service_history_none():
    """
    Test Case 5: Service history none -> multiplier 0.70 applied
    """
    stage7 = {
        "asking_price": 20000,
        "estimated_market_price_p50": 20000,
        "comps_used_count": 60
    }
    stage4 = {
        "risk_level_overall": "medium",
        "signals": {},
        "service_history_level": "none",
        "extraction_warnings": []
    }

    result = calculate_flipability(stage7, stage4)
    
    components = result["components"]
    
    assert components["risk_multiplier"] == 0.70
    assert len(result["penalties_applied"]) == 1
    assert result["penalties_applied"][0]["type"] == "service_history_none"
