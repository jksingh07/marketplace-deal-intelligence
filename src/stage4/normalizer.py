"""
Signal Normalizer Module for Stage 4

Centralizes all value normalization and mapping logic.
Handles LLM output variations gracefully without rejecting valid semantic content.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from common.schema_enums import (
    get_all_signal_types,
    get_evidence_present_types,
    get_maintenance_claim_types,
    get_red_flag_types,
    is_valid_signal_type,
    is_valid_evidence_present,
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Value Mapping Tables
# ============================================================================

# Maps common LLM variations to valid evidence_present values
EVIDENCE_PRESENT_MAPPING: Dict[str, str] = {
    # Logbook variations
    "service_book": "logbook",
    "service_logbook": "logbook",
    "log_book": "logbook",
    "service_history": "logbook",
    "full_service_history": "logbook",
    "fsh": "logbook",
    "log": "logbook",
    "books": "logbook",
    "service_record": "logbook",
    "service_records": "logbook",
    # Receipt variations
    "receipt": "receipts",
    "service_receipts": "receipts",
    "maintenance_receipts": "receipts",
    "reciepts": "receipts",  # Common typo
    "invoices": "receipts",
    # Workshop invoice variations
    "invoice": "workshop_invoice",
    "service_invoice": "workshop_invoice",
    "mechanic_invoice": "workshop_invoice",
    "workshop_invoices": "workshop_invoice",
    "garage_invoice": "workshop_invoice",
    # Photo variations
    "photos": "photos_of_records",
    "photo": "photos_of_records",
    "pictures": "photos_of_records",
    "images": "photos_of_records",
    "pics": "photos_of_records",
    "documentation_photos": "photos_of_records",
    # None variations
    "no_records": "none",
    "no_evidence": "none",
    "unknown": "none",
    "n/a": "none",
    "na": "none",
    "not_provided": "none",
}

# Maps common signal type variations to valid types
# Format: { (category, variation): valid_type }
SIGNAL_TYPE_MAPPING: Dict[tuple, str] = {
    # Legality mappings
    ("legality", "no_registration"): "no_rego",
    ("legality", "unregistered"): "unregistered",
    ("legality", "expired_rego"): "rego_expired",
    ("legality", "no_roadworthy"): "no_rwc",
    ("legality", "needs_roadworthy"): "rwc_required",
    ("legality", "defect"): "defected",
    ("legality", "defect_notice"): "defected",
    
    # Accident history mappings
    ("accident_history", "write_off"): "writeoff",
    ("accident_history", "written_off"): "writeoff",
    ("accident_history", "total_loss"): "writeoff",
    ("accident_history", "totaled"): "writeoff",
    ("accident_history", "salvage"): "salvage_title",
    ("accident_history", "rebuilt"): "rebuilt_title",
    ("accident_history", "flooded"): "flood_damage",
    ("accident_history", "water_damaged"): "flood_damage",
    ("accident_history", "accident"): "accident_damage",
    ("accident_history", "crash_damage"): "accident_damage",
    ("accident_history", "hail"): "hail_damage",
    
    # Mechanical mappings
    ("mechanical_issues", "knocking"): "engine_knock",
    ("mechanical_issues", "overheating"): "engine_overheating",
    ("mechanical_issues", "runs_hot"): "engine_overheating",
    ("mechanical_issues", "leaking_oil"): "oil_leak",
    ("mechanical_issues", "head_gasket"): "head_gasket_suspected",
    ("mechanical_issues", "blown_head_gasket"): "head_gasket_suspected",
    ("mechanical_issues", "transmission_issue"): "gearbox_issue",
    ("mechanical_issues", "trans_problem"): "gearbox_issue",
    ("mechanical_issues", "wont_start"): "starting_issue",
    ("mechanical_issues", "doesnt_start"): "not_running",
    ("mechanical_issues", "dead"): "not_running",
    ("mechanical_issues", "engine_light"): "check_engine_light",
    ("mechanical_issues", "cel"): "check_engine_light",
    
    # Mods performance mappings
    ("mods_performance", "tune"): "tuned",
    ("mods_performance", "remapped"): "ecu_tune",
    ("mods_performance", "remap"): "ecu_tune",
    ("mods_performance", "stage1"): "stage_1",
    ("mods_performance", "stage_1_tune"): "stage_1",
    ("mods_performance", "stage2"): "stage_2_or_higher",
    ("mods_performance", "stage_2"): "stage_2_or_higher",
    ("mods_performance", "stage3"): "stage_2_or_higher",
    ("mods_performance", "big_turbo"): "turbo_upgrade",
    ("mods_performance", "upgraded_turbo"): "turbo_upgrade",
    ("mods_performance", "ethanol"): "e85_flex_fuel",
    ("mods_performance", "flex_fuel"): "e85_flex_fuel",
    ("mods_performance", "track_car"): "track_use",
    ("mods_performance", "race_car"): "race_build",
    
    # Seller behavior mappings
    ("seller_behavior", "need_sold"): "need_gone",
    ("seller_behavior", "must_go"): "need_gone",
    ("seller_behavior", "fixed_price"): "firm_price",
    ("seller_behavior", "price_firm"): "firm_price",
    ("seller_behavior", "negotiable"): "open_to_offers",
    ("seller_behavior", "ono"): "open_to_offers",
    ("seller_behavior", "or_nearest_offer"): "open_to_offers",
    ("seller_behavior", "swaps"): "swap_trade",
    ("seller_behavior", "trades"): "swap_trade",
}

# Maps common LLM maintenance claim type variations to valid schema values
# Valid types: serviced_recently, regular_service_claimed, logbook_mentioned,
#   receipts_mentioned, major_service_done, timing_belt_done, water_pump_done,
#   clutch_replaced, gearbox_rebuilt, engine_rebuilt, new_tyres, new_brakes, battery_replaced
MAINTENANCE_CLAIM_MAPPING: Dict[str, str] = {
    # Service history variations
    "service_history": "regular_service_claimed",
    "service_completed": "serviced_recently",
    "serviced": "serviced_recently",
    "recent_service": "serviced_recently",
    "just_serviced": "serviced_recently",
    "full_service": "regular_service_claimed",
    "full_service_history": "regular_service_claimed",
    "regular_service": "regular_service_claimed",
    "regular_servicing": "regular_service_claimed",
    "dealer_serviced": "regular_service_claimed",
    # Logbook variations
    "logbook": "logbook_mentioned",
    "log_book": "logbook_mentioned",
    "service_book": "logbook_mentioned",
    "has_logbook": "logbook_mentioned",
    # Receipts variations
    "receipts": "receipts_mentioned",
    "has_receipts": "receipts_mentioned",
    "service_receipts": "receipts_mentioned",
    # Major service variations
    "major_service": "major_service_done",
    "timing_belt": "timing_belt_done",
    "timing_belt_replaced": "timing_belt_done",
    "water_pump": "water_pump_done",
    "water_pump_replaced": "water_pump_done",
    # Parts replaced variations
    "clutch": "clutch_replaced",
    "new_clutch": "clutch_replaced",
    "gearbox": "gearbox_rebuilt",
    "transmission": "gearbox_rebuilt",
    "engine": "engine_rebuilt",
    "rebuilt_engine": "engine_rebuilt",
    "new_engine": "engine_rebuilt",
    "tyres": "new_tyres",
    "tires": "new_tyres",
    "new_tires": "new_tyres",
    "brakes": "new_brakes",
    "brake_pads": "new_brakes",
    "battery": "battery_replaced",
    "new_battery": "battery_replaced",
}

# Valid maintenance claim types from schema (including "other" for unknown types)
VALID_MAINTENANCE_CLAIM_TYPES = {
    "serviced_recently", "regular_service_claimed", "logbook_mentioned",
    "receipts_mentioned", "major_service_done", "timing_belt_done",
    "water_pump_done", "clutch_replaced", "gearbox_rebuilt",
    "engine_rebuilt", "new_tyres", "new_brakes", "battery_replaced",
    "other"  # Fallback for unknown types
}


class SignalNormalizer:
    """
    Normalizes LLM output values to valid schema values.
    
    Provides graceful handling of variations without rejecting valid data.
    """
    
    def __init__(self):
        """Initialize normalizer with schema-loaded valid values."""
        self._valid_signal_types = get_all_signal_types()
        self._valid_evidence_present = get_evidence_present_types()
        self._valid_claim_types = get_maintenance_claim_types()
        self._valid_red_flag_types = get_red_flag_types()
    
    def normalize_signal_type(
        self,
        signal_type: str,
        category: str,
    ) -> str:
        """
        Normalize a signal type to a valid schema value.
        
        NEVER returns None - unknown types are mapped to "other".
        This ensures we never lose valid semantic content.
        
        Args:
            signal_type: Raw signal type from LLM
            category: Signal category name
            
        Returns:
            Valid signal type (uses "other" for unknown types)
        """
        if not signal_type:
            return "other"
        
        if not category:
            return "other"
        
        type_lower = signal_type.lower().strip().replace(" ", "_").replace("-", "_")
        
        # Check if already valid
        valid_types = self._valid_signal_types.get(category, set())
        if type_lower in valid_types:
            return type_lower
        
        # Try mapping
        mapping_key = (category, type_lower)
        if mapping_key in SIGNAL_TYPE_MAPPING:
            mapped = SIGNAL_TYPE_MAPPING[mapping_key]
            logger.debug(f"Mapped signal type '{signal_type}' -> '{mapped}'")
            return mapped
        
        # Check if original (non-lowercased) is valid
        if signal_type in valid_types:
            return signal_type
        
        # FALLBACK: Use "other" instead of rejecting
        # This ensures we never lose valid semantic content from LLM
        logger.info(f"Unknown signal type '{signal_type}' for category '{category}' -> using 'other'")
        return "other"
    
    def normalize_evidence_present(
        self,
        value: Any,
    ) -> str:
        """
        Normalize an evidence_present value.
        
        NEVER returns None - unknown values are mapped to "other".
        
        Args:
            value: Raw value from LLM (may be string or dict)
            
        Returns:
            Valid evidence_present value (uses "other" for unknown values)
        """
        # Extract string from dict if needed
        if isinstance(value, dict):
            value = value.get("type", value.get("value", ""))
        
        if not isinstance(value, str) or not value:
            return "other"
        
        value_lower = value.lower().strip().replace(" ", "_").replace("-", "_")
        
        # Check if already valid
        if value_lower in self._valid_evidence_present:
            return value_lower
        
        # Try mapping
        if value_lower in EVIDENCE_PRESENT_MAPPING:
            mapped = EVIDENCE_PRESENT_MAPPING[value_lower]
            logger.debug(f"Mapped evidence_present '{value}' -> '{mapped}'")
            return mapped
        
        # FALLBACK: Use "other" instead of None
        logger.info(f"Unknown evidence_present value '{value}' -> using 'other'")
        return "other"
    
    def normalize_evidence_present_list(
        self,
        evidence_list: List[Any],
    ) -> List[str]:
        """
        Normalize a list of evidence_present values.
        
        All items are preserved (unknown values -> "other").
        
        Args:
            evidence_list: Raw list from LLM
            
        Returns:
            List of valid, deduplicated values
        """
        if not evidence_list:
            return []
        
        normalized = set()
        for item in evidence_list:
            # Skip empty items
            if item is None or item == "":
                continue
            result = self.normalize_evidence_present(item)
            # Only add non-"other" results or if it's the only item
            if result != "other" or len(evidence_list) == 1:
                normalized.add(result)
        
        # Don't return just ["other"] if there were multiple items
        # (that would lose information about what was there)
        if normalized == {"other"} and len(evidence_list) > 1:
            return []
        
        return list(normalized)
    
    def normalize_signal(
        self,
        signal: Dict[str, Any],
        category: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize a complete signal object.
        
        All signals with evidence_text are preserved (unknown types -> "other").
        Only signals without evidence_text are filtered out.
        
        Args:
            signal: Raw signal dict from LLM
            category: Signal category
            
        Returns:
            Normalized signal or None only if evidence_text is missing
        """
        if not signal or not isinstance(signal, dict):
            return None
        
        # Evidence is required - this is the only thing that invalidates a signal
        evidence_text = signal.get("evidence_text", "")
        if not evidence_text:
            return None
        
        # Normalize type - always succeeds (uses "other" for unknown)
        raw_type = signal.get("type", "")
        normalized_type = self.normalize_signal_type(raw_type, category)
        
        # Create normalized signal with only allowed properties
        normalized = {
            "type": normalized_type,
            "severity": signal.get("severity", "medium"),
            "verification_level": signal.get("verification_level", "inferred"),
            "evidence_text": evidence_text,
            "confidence": signal.get("confidence", 0.5),
        }
        
        # Ensure severity is valid
        severity = str(normalized["severity"]).lower()
        if severity not in {"low", "medium", "high"}:
            normalized["severity"] = "medium"
        else:
            normalized["severity"] = severity
        
        # Ensure verification_level is valid
        verification = str(normalized["verification_level"]).lower()
        if verification not in {"verified", "inferred"}:
            normalized["verification_level"] = "inferred"
        else:
            normalized["verification_level"] = verification
        
        # Ensure confidence is in valid range
        confidence = normalized["confidence"]
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        normalized["confidence"] = max(0.0, min(1.0, float(confidence)))
        
        return normalized
    
    def normalize_signals(
        self,
        signals: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Normalize all signals in a signals dictionary.
        
        Args:
            signals: Raw signals dict from LLM
            
        Returns:
            Normalized signals dict with only valid signals
        """
        normalized = {}
        
        for category in ["legality", "accident_history", "mechanical_issues",
                         "cosmetic_issues", "mods_performance", "mods_cosmetic",
                         "seller_behavior"]:
            raw_list = signals.get(category, [])
            normalized_list = []
            
            for signal in raw_list:
                result = self.normalize_signal(signal, category)
                if result:
                    normalized_list.append(result)
            
            normalized[category] = normalized_list
        
        return normalized
    
    def normalize_maintenance_claim_type(
        self,
        claim_type: str,
    ) -> str:
        """
        Normalize a maintenance claim type to a valid schema value.
        
        NEVER returns None - unknown types are mapped to "other".
        
        Args:
            claim_type: Raw claim type from LLM
            
        Returns:
            Valid claim type (uses "other" for unknown types)
        """
        if not claim_type:
            return "other"
        
        type_lower = claim_type.lower().strip().replace(" ", "_").replace("-", "_")
        
        # Check if already valid
        if type_lower in VALID_MAINTENANCE_CLAIM_TYPES:
            return type_lower
        
        # Try mapping
        if type_lower in MAINTENANCE_CLAIM_MAPPING:
            mapped = MAINTENANCE_CLAIM_MAPPING[type_lower]
            logger.debug(f"Mapped maintenance claim type '{claim_type}' -> '{mapped}'")
            return mapped
        
        # FALLBACK: Use "other" instead of rejecting
        logger.info(f"Unknown maintenance claim type '{claim_type}' -> using 'other'")
        return "other"
    
    def normalize_maintenance_claim(
        self,
        claim: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize a single maintenance claim.
        
        Ensures:
        - type is valid (uses "other" for unknown types)
        - required fields exist (type, details, evidence_text, confidence, verification_level)
        - no extra properties (removes severity if present)
        
        Args:
            claim: Raw claim dict from LLM
            
        Returns:
            Normalized claim or None only if evidence_text is missing
        """
        if not claim or not isinstance(claim, dict):
            return None
        
        # Get evidence_text (required - this is the only thing that makes a claim invalid)
        evidence_text = claim.get("evidence_text", "")
        if not evidence_text:
            return None
        
        # Normalize type - always succeeds (uses "other" for unknown)
        raw_type = claim.get("type", "")
        normalized_type = self.normalize_maintenance_claim_type(raw_type)
        
        # Build normalized claim with only allowed properties
        normalized = {
            "type": normalized_type,
            "details": claim.get("details"),  # Can be null
            "evidence_text": evidence_text,
            "confidence": max(0.0, min(1.0, float(claim.get("confidence", 0.5)))),
            "verification_level": claim.get("verification_level", "inferred"),
        }
        
        # Ensure verification_level is valid
        if normalized["verification_level"] not in {"verified", "inferred"}:
            normalized["verification_level"] = "inferred"
        
        return normalized
    
    def normalize_red_flag_type(
        self,
        flag_type: str,
    ) -> str:
        """
        Normalize a red flag type to a valid schema value.
        
        NEVER returns None - unknown types are mapped to "other".
        
        Args:
            flag_type: Raw red flag type from LLM
            
        Returns:
            Valid red flag type (uses "other" for unknown types)
        """
        if not flag_type:
            return "other"
        
        type_lower = flag_type.lower().strip().replace(" ", "_").replace("-", "_")
        
        # Valid red flag types from schema
        valid_types = {
            "claim_without_proof",
            "major_work_no_receipts",
            "inconsistent_service_story",
            "recent_issue_disguised_as_minor",
            "odometer_or_history_unclear",
            "other"
        }
        
        if type_lower in valid_types:
            return type_lower
        
        # FALLBACK: Use "other" instead of rejecting
        logger.info(f"Unknown red flag type '{flag_type}' -> using 'other'")
        return "other"
    
    def normalize_red_flag(
        self,
        flag: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize a single red flag.
        
        Args:
            flag: Raw red flag dict from LLM
            
        Returns:
            Normalized red flag or None only if evidence_text is missing
        """
        if not flag or not isinstance(flag, dict):
            return None
        
        # Get evidence_text (required)
        evidence_text = flag.get("evidence_text", "")
        if not evidence_text:
            return None
        
        # Normalize type - always succeeds
        raw_type = flag.get("type", "")
        normalized_type = self.normalize_red_flag_type(raw_type)
        
        # Build normalized red flag with required properties
        normalized = {
            "type": normalized_type,
            "severity": flag.get("severity", "medium"),
            "verification_level": flag.get("verification_level", "inferred"),
            "evidence_text": evidence_text,
            "confidence": max(0.0, min(1.0, float(flag.get("confidence", 0.5)))),
        }
        
        # Ensure severity is valid
        if normalized["severity"] not in {"low", "medium", "high"}:
            normalized["severity"] = "medium"
        
        # Ensure verification_level is valid
        if normalized["verification_level"] not in {"verified", "inferred"}:
            normalized["verification_level"] = "inferred"
        
        return normalized
    
    def normalize_missing_info_type(
        self,
        missing_type: str,
    ) -> str:
        """
        Normalize a missing_info type to a valid schema value.
        
        NEVER returns None - unknown types are mapped to "other".
        
        Args:
            missing_type: Raw missing_info type from LLM
            
        Returns:
            Valid missing_info type (uses "other" for unknown types)
        """
        if not missing_type:
            return "other"
        
        type_lower = missing_type.lower().strip().replace(" ", "_").replace("-", "_")
        
        # Valid missing_info types from schema
        valid_types = {
            "vin_unknown",
            "ppsr_or_finance_status_unknown",
            "rego_expiry_unknown",
            "rwc_status_unknown",
            "accident_history_unknown",
            "service_history_unknown",
            "number_of_owners_unknown",
            "reason_for_selling_unknown",
            "recent_repairs_proof_unknown",
            "mods_engineered_unknown",
            "inspection_availability_unknown",
            "other"
        }
        
        if type_lower in valid_types:
            return type_lower
        
        # Try mapping common variations
        mapping = {
            "service_history_none": "service_history_unknown",
            "no_service_history": "service_history_unknown",
            "service_history_missing": "service_history_unknown",
            "rwc_status_none": "rwc_status_unknown",
            "no_rwc_info": "rwc_status_unknown",
        }
        
        if type_lower in mapping:
            mapped = mapping[type_lower]
            logger.debug(f"Mapped missing_info type '{missing_type}' -> '{mapped}'")
            return mapped
        
        # FALLBACK: Use "other" instead of rejecting
        logger.info(f"Unknown missing_info type '{missing_type}' -> using 'other'")
        return "other"
    
    def normalize_missing_info_list(
        self,
        missing_list: List[str],
    ) -> List[str]:
        """
        Normalize a list of missing_info values.
        
        All items are preserved (unknown values -> "other").
        
        Args:
            missing_list: Raw list from LLM
            
        Returns:
            List of valid, deduplicated values
        """
        if not missing_list:
            return []
        
        normalized = set()
        for item in missing_list:
            if not item or not isinstance(item, str):
                continue
            result = self.normalize_missing_info_type(item)
            # Only add non-"other" results or if it's the only item
            if result != "other" or len(missing_list) == 1:
                normalized.add(result)
        
        # Don't return just ["other"] if there were multiple items
        if normalized == {"other"} and len(missing_list) > 1:
            return []
        
        return list(normalized)
    
    def normalize_maintenance(
        self,
        maintenance: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Normalize maintenance section.
        
        All items with evidence_text are preserved (unknown types -> "other").
        Only items without evidence_text are filtered out.
        
        Args:
            maintenance: Raw maintenance dict from LLM
            
        Returns:
            Normalized maintenance dict
        """
        if not maintenance:
            return {
                "claims": [],
                "evidence_present": [],
                "red_flags": [],
            }
        
        # Normalize claims - only filtered if no evidence_text
        raw_claims = maintenance.get("claims", [])
        normalized_claims = []
        for claim in raw_claims:
            normalized = self.normalize_maintenance_claim(claim)
            if normalized:
                normalized_claims.append(normalized)
        
        # Normalize red_flags - only filtered if no evidence_text
        raw_red_flags = maintenance.get("red_flags", [])
        normalized_red_flags = []
        for flag in raw_red_flags:
            normalized = self.normalize_red_flag(flag)
            if normalized:
                normalized_red_flags.append(normalized)
        
        return {
            "claims": normalized_claims,
            "evidence_present": self.normalize_evidence_present_list(
                maintenance.get("evidence_present", [])
            ),
            "red_flags": normalized_red_flags,
        }


# Module-level singleton for convenience
_normalizer: Optional[SignalNormalizer] = None


def get_normalizer() -> SignalNormalizer:
    """Get the singleton normalizer instance."""
    global _normalizer
    if _normalizer is None:
        _normalizer = SignalNormalizer()
    return _normalizer


# Convenience functions
def normalize_signal_type(signal_type: str, category: str) -> Optional[str]:
    """Normalize a signal type to a valid schema value."""
    return get_normalizer().normalize_signal_type(signal_type, category)


def normalize_evidence_present(value: Any) -> Optional[str]:
    """Normalize an evidence_present value."""
    return get_normalizer().normalize_evidence_present(value)


def normalize_evidence_present_list(evidence_list: List[Any]) -> List[str]:
    """Normalize a list of evidence_present values."""
    return get_normalizer().normalize_evidence_present_list(evidence_list)


def normalize_signals(signals: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """Normalize all signals in a signals dictionary."""
    return get_normalizer().normalize_signals(signals)


def normalize_maintenance(maintenance: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize maintenance section."""
    return get_normalizer().normalize_maintenance(maintenance)


def normalize_missing_info_list(missing_list: List[str]) -> List[str]:
    """Normalize a list of missing_info values."""
    return get_normalizer().normalize_missing_info_list(missing_list)
