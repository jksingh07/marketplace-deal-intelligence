"""
Tests for Evidence Verification.

Tests that:
- Exact match evidence passes
- Paraphrased evidence is rejected
- Case-insensitive matching works
- Verified vs inferred classification is correct
"""

import pytest

from stage4.evidence_verifier import (
    verify_signals,
    verify_single_signal,
    check_evidence_exists,
    is_explicit_evidence,
    classify_verification_level,
)
from stage4.text_prep import check_evidence_exists


class TestEvidenceExists:
    """Test evidence existence checking."""
    
    def test_exact_match_found(self):
        """Test that exact match is found."""
        evidence = "the car is defected"
        original = "Selling my car. The car is defected. Price is firm."
        
        assert check_evidence_exists(evidence, original)
    
    def test_case_insensitive_match(self):
        """Test case-insensitive matching."""
        evidence = "DEFECTED"
        original = "The car is defected due to exhaust."
        
        assert check_evidence_exists(evidence, original)
    
    def test_whitespace_normalized(self):
        """Test whitespace normalization in matching."""
        evidence = "needs  work"
        original = "This car needs work on the engine."
        
        assert check_evidence_exists(evidence, original)
    
    def test_not_found_returns_false(self):
        """Test that non-existent evidence returns False."""
        evidence = "write off"
        original = "Perfect condition, no issues."
        
        assert not check_evidence_exists(evidence, original)
    
    def test_partial_word_not_matched(self):
        """Test that partial word matches within other words work."""
        evidence = "tuned"
        original = "The car has been finely tuned by a mechanic."
        
        assert check_evidence_exists(evidence, original)


class TestVerifySingleSignal:
    """Test single signal verification."""
    
    def test_signal_with_valid_evidence_passes(self):
        """Test signal with valid evidence passes."""
        signal = {
            "type": "defected",
            "severity": "high",
            "verification_level": "verified",
            "evidence_text": "car is defected",
            "confidence": 0.9,
        }
        original = "The car is defected. Needs clearance."
        
        result = verify_single_signal(signal, original)
        
        assert result is not None
        assert result["type"] == "defected"
    
    def test_signal_without_evidence_rejected(self):
        """Test signal without evidence is rejected."""
        signal = {
            "type": "defected",
            "severity": "high",
            "verification_level": "verified",
            "evidence_text": "",
            "confidence": 0.9,
        }
        original = "The car is defected."
        
        result = verify_single_signal(signal, original)
        
        assert result is None
    
    def test_signal_with_hallucinated_evidence_rejected(self):
        """Test signal with non-existent evidence is rejected."""
        signal = {
            "type": "writeoff",
            "severity": "high",
            "verification_level": "verified",
            "evidence_text": "this is a write off",
            "confidence": 0.95,
        }
        original = "Perfect condition car, no issues whatsoever."
        
        result = verify_single_signal(signal, original)
        
        assert result is None


class TestExplicitEvidence:
    """Test explicit vs implicit evidence classification."""
    
    def test_writeoff_is_explicit(self):
        """Test 'write off' is classified as explicit."""
        assert is_explicit_evidence("the car is a write off", "accident_history")
    
    def test_defected_is_explicit(self):
        """Test 'defected' is classified as explicit."""
        assert is_explicit_evidence("car has been defected", "legality")
    
    def test_needs_love_is_implicit(self):
        """Test 'needs love' is classified as implicit."""
        assert not is_explicit_evidence("needs a bit of love", "mechanical")
    
    def test_easy_fix_is_implicit(self):
        """Test 'easy fix' is classified as implicit."""
        assert not is_explicit_evidence("easy fix for a mechanic", "mechanical")
    
    def test_tuned_is_explicit(self):
        """Test 'tuned' is classified as explicit."""
        assert is_explicit_evidence("car has been tuned", "mods_performance")
    
    def test_stage_2_is_explicit(self):
        """Test 'stage 2' is classified as explicit."""
        assert is_explicit_evidence("Running stage 2 tune", "mods_performance")


class TestClassifyVerificationLevel:
    """Test verification level classification."""
    
    def test_explicit_gets_verified(self):
        """Test explicit evidence gets verified level."""
        level, confidence = classify_verification_level(
            "the car is defected",
            "legality",
            0.7,
        )
        
        assert level == "verified"
        assert confidence >= 0.9
    
    def test_implicit_gets_inferred(self):
        """Test implicit evidence gets inferred level."""
        level, confidence = classify_verification_level(
            "needs a bit of love",
            "mechanical",
            0.7,
        )
        
        assert level == "inferred"
        assert confidence < 0.9


class TestVerifySignals:
    """Test full signal verification on extraction result."""
    
    def test_extraction_result_verified(self):
        """Test full extraction result gets signals verified."""
        extraction_result = {
            "payload": {
                "signals": {
                    "legality": [
                        {
                            "type": "defected",
                            "severity": "high",
                            "verification_level": "verified",
                            "evidence_text": "car is defected",
                            "confidence": 0.9,
                        },
                        {
                            "type": "no_rego",
                            "severity": "high",
                            "verification_level": "verified",
                            "evidence_text": "this evidence does not exist",
                            "confidence": 0.9,
                        },
                    ],
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
            }
        }
        original = "The car is defected. Price negotiable."
        
        result = verify_signals(extraction_result, original)
        
        # Should keep defected (evidence exists)
        # Should reject no_rego (evidence doesn't exist)
        assert len(result["payload"]["signals"]["legality"]) == 1
        assert result["payload"]["signals"]["legality"][0]["type"] == "defected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
