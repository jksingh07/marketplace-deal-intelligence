"""
Tests for Stage 4 Schema Validation.

Tests that:
- Valid outputs pass validation
- Missing required fields fail
- Invalid enum values fail
- Invalid confidence ranges fail
"""

import pytest
from datetime import datetime, timezone

from stage4.schema_validator import (
    validate_stage4_output,
    validate_or_raise,
    create_minimal_valid_output,
    load_schema,
)


class TestSchemaValidation:
    """Test suite for schema validation."""
    
    def test_schema_loads(self):
        """Test that schema file can be loaded."""
        schema = load_schema()
        assert schema is not None
        assert "$schema" in schema
        assert "properties" in schema
    
    def test_minimal_valid_output_passes(self):
        """Test that minimal valid output passes validation."""
        output = create_minimal_valid_output(
            listing_id="test123",
            source_snapshot_id="snap123",
        )
        
        is_valid, errors = validate_stage4_output(output)
        
        assert is_valid, f"Validation failed: {errors}"
        assert len(errors) == 0
    
    def test_missing_listing_id_fails(self):
        """Test that missing listing_id fails validation."""
        output = create_minimal_valid_output(
            listing_id="test123",
            source_snapshot_id="snap123",
        )
        del output["listing_id"]
        
        is_valid, errors = validate_stage4_output(output)
        
        assert not is_valid
        assert any("listing_id" in e for e in errors)
    
    def test_missing_payload_fails(self):
        """Test that missing payload fails validation."""
        output = create_minimal_valid_output(
            listing_id="test123",
            source_snapshot_id="snap123",
        )
        del output["payload"]
        
        is_valid, errors = validate_stage4_output(output)
        
        assert not is_valid
        assert any("payload" in e for e in errors)
    
    def test_invalid_severity_enum_fails(self):
        """Test that invalid severity enum value fails."""
        output = create_minimal_valid_output(
            listing_id="test123",
            source_snapshot_id="snap123",
        )
        
        # Add signal with invalid severity
        output["payload"]["signals"]["legality"].append({
            "type": "defected",
            "severity": "invalid_severity",  # Invalid!
            "verification_level": "verified",
            "evidence_text": "test evidence",
            "confidence": 0.9,
        })
        
        is_valid, errors = validate_stage4_output(output)
        
        assert not is_valid
    
    def test_invalid_verification_level_fails(self):
        """Test that invalid verification_level fails."""
        output = create_minimal_valid_output(
            listing_id="test123",
            source_snapshot_id="snap123",
        )
        
        output["payload"]["signals"]["legality"].append({
            "type": "defected",
            "severity": "high",
            "verification_level": "maybe",  # Invalid!
            "evidence_text": "test evidence",
            "confidence": 0.9,
        })
        
        is_valid, errors = validate_stage4_output(output)
        
        assert not is_valid
    
    def test_confidence_below_zero_fails(self):
        """Test that confidence < 0 fails."""
        output = create_minimal_valid_output(
            listing_id="test123",
            source_snapshot_id="snap123",
        )
        
        output["payload"]["signals"]["legality"].append({
            "type": "defected",
            "severity": "high",
            "verification_level": "verified",
            "evidence_text": "test evidence",
            "confidence": -0.1,  # Invalid!
        })
        
        is_valid, errors = validate_stage4_output(output)
        
        assert not is_valid
    
    def test_confidence_above_one_fails(self):
        """Test that confidence > 1 fails."""
        output = create_minimal_valid_output(
            listing_id="test123",
            source_snapshot_id="snap123",
        )
        
        output["payload"]["signals"]["legality"].append({
            "type": "defected",
            "severity": "high",
            "verification_level": "verified",
            "evidence_text": "test evidence",
            "confidence": 1.5,  # Invalid!
        })
        
        is_valid, errors = validate_stage4_output(output)
        
        assert not is_valid
    
    def test_empty_evidence_text_fails(self):
        """Test that empty evidence_text fails."""
        output = create_minimal_valid_output(
            listing_id="test123",
            source_snapshot_id="snap123",
        )
        
        output["payload"]["signals"]["legality"].append({
            "type": "defected",
            "severity": "high",
            "verification_level": "verified",
            "evidence_text": "",  # Invalid!
            "confidence": 0.9,
        })
        
        is_valid, errors = validate_stage4_output(output)
        
        assert not is_valid
    
    def test_valid_signal_passes(self):
        """Test that properly formed signal passes."""
        output = create_minimal_valid_output(
            listing_id="test123",
            source_snapshot_id="snap123",
        )
        
        output["payload"]["signals"]["legality"].append({
            "type": "defected",
            "severity": "high",
            "verification_level": "verified",
            "evidence_text": "Car has been defected",
            "confidence": 0.95,
        })
        
        is_valid, errors = validate_stage4_output(output)
        
        assert is_valid, f"Validation failed: {errors}"
    
    def test_validate_or_raise_raises(self):
        """Test that validate_or_raise raises on invalid output."""
        output = {"invalid": "output"}
        
        with pytest.raises(Exception):
            validate_or_raise(output)
    
    def test_invalid_risk_level_overall_fails(self):
        """Test that invalid risk_level_overall fails."""
        output = create_minimal_valid_output(
            listing_id="test123",
            source_snapshot_id="snap123",
        )
        output["payload"]["risk_level_overall"] = "very_high"  # Invalid!
        
        is_valid, errors = validate_stage4_output(output)
        
        assert not is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
