"""
Tests for Idempotency.

Tests that:
- Same input + same snapshot_id = same output structure
- Re-running doesn't change signal types
- Guardrails produce consistent results
"""

import pytest
import json

from stage4.runner import run_stage4, run_guardrails_only
from stage4.text_prep import normalize_text
from stage4.guardrails import run_guardrails


class TestGuardrailIdempotency:
    """Test guardrail rules produce consistent results."""
    
    def test_guardrails_same_input_same_output(self):
        """Test guardrails produce same output for same input."""
        text = normalize_text(
            "Subaru WRX",
            "Stage 2 tune, defected for exhaust, needs RWC."
        )
        
        result1 = run_guardrails(text)
        result2 = run_guardrails(text)
        
        # Should produce identical signal structures
        assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)
    
    def test_guardrails_multiple_runs_stable(self):
        """Test multiple guardrail runs are stable."""
        text = normalize_text(
            "Evo",
            "Write off, not running, E85 tuned track car."
        )
        
        results = [run_guardrails(text) for _ in range(5)]
        
        # All results should be identical
        first_json = json.dumps(results[0], sort_keys=True)
        for result in results[1:]:
            assert json.dumps(result, sort_keys=True) == first_json
    
    def test_signal_types_stable(self):
        """Test signal types don't change between runs."""
        text = normalize_text(
            "BMW",
            "Has overheating issue and gearbox problem."
        )
        
        result1 = run_guardrails(text)
        result2 = run_guardrails(text)
        
        types1 = {s["type"] for s in result1["mechanical_issues"]}
        types2 = {s["type"] for s in result2["mechanical_issues"]}
        
        assert types1 == types2


class TestPipelineIdempotency:
    """Test full pipeline produces consistent results (without LLM)."""
    
    def test_pipeline_skip_llm_idempotent(self):
        """Test pipeline with skip_llm produces stable output."""
        listing = {
            "listing_id": "test123",
            "title": "Defected WRX",
            "description": "Car is defected, needs RWC. Stage 2 tune.",
        }
        
        # Run twice with skip_llm
        result1 = run_stage4(listing, skip_llm=True, validate=True)
        result2 = run_stage4(listing, skip_llm=True, validate=True)
        
        # Compare relevant fields (not created_at which will differ)
        assert result1["listing_id"] == result2["listing_id"]
        assert result1["payload"]["risk_level_overall"] == result2["payload"]["risk_level_overall"]
        assert result1["payload"]["signals"] == result2["payload"]["signals"]
    
    def test_pipeline_guardrails_only_stable(self):
        """Test guardrails-only mode is stable."""
        listing = {
            "listing_id": "stable_test",
            "title": "Flood damaged car",
            "description": "Flood damage, salvage title, not running.",
        }
        
        result1 = run_guardrails_only(listing)
        result2 = run_guardrails_only(listing)
        
        assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)


class TestTextNormalizationIdempotency:
    """Test text normalization is idempotent."""
    
    def test_normalize_text_idempotent(self):
        """Test normalize_text produces same result."""
        title = "Test  Car"
        description = "Has   extra   spaces."
        
        result1 = normalize_text(title, description)
        result2 = normalize_text(title, description)
        
        assert result1.combined_text == result2.combined_text
        assert result1.normalized_text == result2.normalized_text
        assert result1.sentences == result2.sentences
    
    def test_whitespace_handling_stable(self):
        """Test whitespace handling is consistent."""
        title = "Test"
        description = "Line 1\n\nLine 2\n\n\nLine 3"
        
        result1 = normalize_text(title, description)
        result2 = normalize_text(title, description)
        
        assert result1.sentences == result2.sentences


class TestSnapshotIdHandling:
    """Test snapshot_id handling for idempotency."""
    
    def test_different_snapshot_ids_different_outputs(self):
        """Test different snapshot_ids produce different output metadata."""
        listing = {
            "listing_id": "test123",
            "title": "Test Car",
            "description": "Test description.",
        }
        
        result1 = run_stage4(listing, source_snapshot_id="snap1", skip_llm=True)
        result2 = run_stage4(listing, source_snapshot_id="snap2", skip_llm=True)
        
        assert result1["source_snapshot_id"] == "snap1"
        assert result2["source_snapshot_id"] == "snap2"
    
    def test_same_snapshot_id_same_key_fields(self):
        """Test same snapshot_id produces same key fields."""
        listing = {
            "listing_id": "test123",
            "title": "Defected car",
            "description": "Car is defected.",
        }
        
        result1 = run_stage4(listing, source_snapshot_id="snap1", skip_llm=True)
        result2 = run_stage4(listing, source_snapshot_id="snap1", skip_llm=True)
        
        # Key fields should match
        assert result1["listing_id"] == result2["listing_id"]
        assert result1["source_snapshot_id"] == result2["source_snapshot_id"]
        assert result1["stage_version"] == result2["stage_version"]
        assert result1["ruleset_version"] == result2["ruleset_version"]


class TestDerivedFieldsIdempotency:
    """Test derived field computation is idempotent."""
    
    def test_risk_level_stable(self):
        """Test risk_level_overall is stable."""
        listing = {
            "listing_id": "risk_test",
            "title": "Write off car",
            "description": "This is a write off vehicle.",
        }
        
        results = [
            run_stage4(listing, skip_llm=True)
            for _ in range(3)
        ]
        
        risk_levels = [r["payload"]["risk_level_overall"] for r in results]
        assert all(rl == risk_levels[0] for rl in risk_levels)
    
    def test_mods_risk_level_stable(self):
        """Test mods_risk_level is stable."""
        listing = {
            "listing_id": "mods_test",
            "title": "Stage 2 GTI",
            "description": "Running stage 2 tune and turbo upgrade.",
        }
        
        results = [
            run_stage4(listing, skip_llm=True)
            for _ in range(3)
        ]
        
        mods_levels = [r["payload"]["mods_risk_level"] for r in results]
        assert all(ml == mods_levels[0] for ml in mods_levels)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
