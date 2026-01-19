"""
Tests for Guardrail Rules.

Tests that:
- "write off" detected as writeoff
- "defected" detected as defected
- "not running" detected as not_running
- "stage 2" detected as stage_2_or_higher
- "E85" detected as e85_flex_fuel
- Clean description produces no false positives
"""

import pytest

from stage4.guardrails import (
    run_guardrails,
    check_high_risk_keywords,
    get_high_severity_types,
)
from stage4.text_prep import normalize_text


class TestWriteoffDetection:
    """Test write-off signal detection."""
    
    def test_write_off_detected(self):
        """Test 'write off' is detected."""
        text = normalize_text(
            "2015 Toyota Camry",
            "Selling as is, this car is a write off. Good for parts."
        )
        
        signals = run_guardrails(text)
        
        accident_signals = signals["accident_history"]
        assert len(accident_signals) > 0
        assert any(s["type"] == "writeoff" for s in accident_signals)
    
    def test_written_off_detected(self):
        """Test 'written off' is detected."""
        text = normalize_text(
            "Honda Civic",
            "Was written off last year, now repaired."
        )
        
        signals = run_guardrails(text)
        
        accident_signals = signals["accident_history"]
        assert any(s["type"] == "writeoff" for s in accident_signals)
    
    def test_repairable_writeoff_detected(self):
        """Test 'repairable write off' is detected."""
        text = normalize_text(
            "Mazda 3",
            "Repairable write-off, minor front damage."
        )
        
        signals = run_guardrails(text)
        
        accident_signals = signals["accident_history"]
        assert any(s["type"] == "repairable_writeoff" for s in accident_signals)
    
    def test_salvage_detected(self):
        """Test 'salvage' is detected."""
        text = normalize_text(
            "BMW 320i",
            "Salvage title vehicle, cheap."
        )
        
        signals = run_guardrails(text)
        
        accident_signals = signals["accident_history"]
        assert any(s["type"] == "salvage_title" for s in accident_signals)


class TestDefectedDetection:
    """Test defect signal detection."""
    
    def test_defected_detected(self):
        """Test 'defected' is detected."""
        text = normalize_text(
            "Subaru WRX",
            "Car has been defected for exhaust. Easy fix."
        )
        
        signals = run_guardrails(text)
        
        legality_signals = signals["legality"]
        assert len(legality_signals) > 0
        assert any(s["type"] == "defected" for s in legality_signals)
    
    def test_defect_detected(self):
        """Test 'defect' is detected."""
        text = normalize_text(
            "Nissan Skyline",
            "Got a defect notice yesterday."
        )
        
        signals = run_guardrails(text)
        
        legality_signals = signals["legality"]
        assert any(s["type"] == "defected" for s in legality_signals)
    
    def test_unregistered_detected(self):
        """Test 'unregistered' is detected."""
        text = normalize_text(
            "Ford Falcon",
            "Selling unregistered, was sitting in shed."
        )
        
        signals = run_guardrails(text)
        
        legality_signals = signals["legality"]
        assert any(s["type"] == "unregistered" for s in legality_signals)
    
    def test_no_rego_detected(self):
        """Test 'no rego' is detected."""
        text = normalize_text(
            "Holden Commodore",
            "No rego, needs RWC."
        )
        
        signals = run_guardrails(text)
        
        legality_signals = signals["legality"]
        assert any(s["type"] == "no_rego" for s in legality_signals)


class TestMechanicalDetection:
    """Test mechanical issue detection."""
    
    def test_not_running_detected(self):
        """Test 'not running' is detected."""
        text = normalize_text(
            "Toyota Corolla",
            "Not running, needs engine work."
        )
        
        signals = run_guardrails(text)
        
        mechanical_signals = signals["mechanical_issues"]
        assert len(mechanical_signals) > 0
        assert any(s["type"] == "not_running" for s in mechanical_signals)
    
    def test_overheating_detected(self):
        """Test 'overheating' is detected."""
        text = normalize_text(
            "Mercedes",
            "Has overheating issue, needs coolant check."
        )
        
        signals = run_guardrails(text)
        
        mechanical_signals = signals["mechanical_issues"]
        assert any(s["type"] == "engine_overheating" for s in mechanical_signals)
    
    def test_engine_knock_detected(self):
        """Test 'engine knock' is detected."""
        text = normalize_text(
            "BMW",
            "Has engine knock on cold start."
        )
        
        signals = run_guardrails(text)
        
        mechanical_signals = signals["mechanical_issues"]
        assert any(s["type"] == "engine_knock" for s in mechanical_signals)
    
    def test_head_gasket_detected(self):
        """Test 'head gasket' is detected."""
        text = normalize_text(
            "Subaru",
            "Suspected head gasket issue."
        )
        
        signals = run_guardrails(text)
        
        mechanical_signals = signals["mechanical_issues"]
        assert any(s["type"] == "head_gasket_suspected" for s in mechanical_signals)


class TestModsDetection:
    """Test performance modification detection."""
    
    def test_stage_2_detected(self):
        """Test 'stage 2' is detected."""
        text = normalize_text(
            "Audi RS3",
            "Running stage 2 APR tune, 400hp."
        )
        
        signals = run_guardrails(text)
        
        mods_signals = signals["mods_performance"]
        assert len(mods_signals) > 0
        assert any(s["type"] == "stage_2_or_higher" for s in mods_signals)
    
    def test_e85_detected(self):
        """Test 'E85' is detected."""
        text = normalize_text(
            "Evo",
            "Tuned on E85, making 500hp."
        )
        
        signals = run_guardrails(text)
        
        mods_signals = signals["mods_performance"]
        assert any(s["type"] == "e85_flex_fuel" for s in mods_signals)
    
    def test_tuned_detected(self):
        """Test 'tuned' is detected."""
        text = normalize_text(
            "Golf GTI",
            "Has been tuned by a reputable shop."
        )
        
        signals = run_guardrails(text)
        
        mods_signals = signals["mods_performance"]
        assert any(s["type"] == "tuned" for s in mods_signals)
    
    def test_turbo_swap_detected(self):
        """Test 'turbo swap' is detected."""
        text = normalize_text(
            "Silvia S15",
            "Has turbo swap, GT35."
        )
        
        signals = run_guardrails(text)
        
        mods_signals = signals["mods_performance"]
        assert any(s["type"] == "turbo_swap" for s in mods_signals)
    
    def test_track_car_detected(self):
        """Test 'track car' is detected."""
        text = normalize_text(
            "Evo IX",
            "Built as a track car, roll cage fitted."
        )
        
        signals = run_guardrails(text)
        
        mods_signals = signals["mods_performance"]
        assert any(s["type"] == "track_use" for s in mods_signals)


class TestCleanDescription:
    """Test that clean descriptions don't produce false positives."""
    
    def test_clean_description_no_signals(self):
        """Test clean description produces no high-risk signals."""
        text = normalize_text(
            "2020 Toyota Camry",
            "One owner, full service history. Excellent condition. "
            "Always garaged. Leather seats, sunroof. Price negotiable."
        )
        
        signals = run_guardrails(text)
        
        # Should have no high-severity signals
        high_severity = []
        for category, signal_list in signals.items():
            for signal in signal_list:
                if signal.get("severity") == "high":
                    high_severity.append(signal)
        
        assert len(high_severity) == 0
    
    def test_no_false_positives_on_similar_words(self):
        """Test no false positives on words similar to triggers."""
        text = normalize_text(
            "Ford Ranger",
            "Running great, never had any issues. Recently serviced. "
            "Perfect for off-road adventures."
        )
        
        signals = run_guardrails(text)
        
        # Should not detect "running" as "not running"
        mechanical = signals["mechanical_issues"]
        assert not any(s["type"] == "not_running" for s in mechanical)


class TestHighRiskKeywords:
    """Test high risk keyword detection."""
    
    def test_detects_write_off(self):
        """Test write off is detected as high risk."""
        assert check_high_risk_keywords("This is a write off")
    
    def test_detects_defected(self):
        """Test defected is detected as high risk."""
        assert check_high_risk_keywords("Car has been defected")
    
    def test_detects_stage_2(self):
        """Test stage 2 is detected as high risk."""
        assert check_high_risk_keywords("Running stage 2 tune")
    
    def test_clean_text_not_flagged(self):
        """Test clean text is not flagged."""
        assert not check_high_risk_keywords("Perfect condition, one owner")


class TestSignalProperties:
    """Test signal properties are correct."""
    
    def test_signals_have_evidence(self):
        """Test all detected signals have evidence."""
        text = normalize_text(
            "Test",
            "Car is defected and also a write off with overheating."
        )
        
        signals = run_guardrails(text)
        
        for category, signal_list in signals.items():
            for signal in signal_list:
                assert "evidence_text" in signal
                assert len(signal["evidence_text"]) > 0
    
    def test_signals_are_verified(self):
        """Test all rule signals are verified."""
        text = normalize_text(
            "Test",
            "Has been defected for loud exhaust."
        )
        
        signals = run_guardrails(text)
        
        for signal in signals["legality"]:
            assert signal["verification_level"] == "verified"
    
    def test_signals_have_high_confidence(self):
        """Test rule signals have high confidence."""
        text = normalize_text(
            "Test",
            "Not running, engine blown."
        )
        
        signals = run_guardrails(text)
        
        for signal in signals["mechanical_issues"]:
            assert signal["confidence"] >= 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
