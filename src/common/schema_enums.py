"""
Schema Enums - Single Source of Truth

This module dynamically loads enum definitions from the JSON schema contract
and provides them as Python sets for use throughout the codebase.

All enum validation should import from this module to prevent drift.
"""

import json
from pathlib import Path
from typing import Dict, Set, Any, List
from functools import lru_cache


# Path to schema file (relative to project root)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = _PROJECT_ROOT / "contracts" / "stage4_description_intel.schema.json"


@lru_cache(maxsize=1)
def load_schema() -> Dict[str, Any]:
    """
    Load the Stage 4 schema from file.
    
    Cached to avoid repeated file reads.
    
    Returns:
        Schema dictionary
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
    """
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema not found at {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def get_enum_values(definition_name: str) -> Set[str]:
    """
    Get enum values from a schema definition.
    
    Args:
        definition_name: Name of the definition in $defs
        
    Returns:
        Set of valid enum values
    """
    schema = load_schema()
    defs = schema.get("$defs", {})
    
    if definition_name not in defs:
        return set()
    
    definition = defs[definition_name]
    enum_values = definition.get("enum", [])
    
    return set(enum_values)


# ============================================================================
# Signal Type Enums (loaded from schema)
# ============================================================================

@lru_cache(maxsize=1)
def get_signal_types_legality() -> Set[str]:
    """Get valid legality signal types."""
    return get_enum_values("signal_legality_type")


@lru_cache(maxsize=1)
def get_signal_types_accident() -> Set[str]:
    """Get valid accident history signal types."""
    return get_enum_values("signal_accident_type")


@lru_cache(maxsize=1)
def get_signal_types_mechanical() -> Set[str]:
    """Get valid mechanical issues signal types."""
    return get_enum_values("signal_mechanical_type")


@lru_cache(maxsize=1)
def get_signal_types_cosmetic() -> Set[str]:
    """Get valid cosmetic issues signal types."""
    return get_enum_values("signal_cosmetic_type")


@lru_cache(maxsize=1)
def get_signal_types_mods_performance() -> Set[str]:
    """Get valid performance modification signal types."""
    return get_enum_values("signal_mods_performance_type")


@lru_cache(maxsize=1)
def get_signal_types_mods_cosmetic() -> Set[str]:
    """Get valid cosmetic modification signal types."""
    return get_enum_values("signal_mods_cosmetic_type")


@lru_cache(maxsize=1)
def get_signal_types_seller_behavior() -> Set[str]:
    """Get valid seller behavior signal types."""
    return get_enum_values("signal_seller_behavior_type")


@lru_cache(maxsize=1)
def get_all_signal_types() -> Dict[str, Set[str]]:
    """
    Get all signal types organized by category.
    
    Returns:
        Dictionary mapping category name to set of valid types
    """
    return {
        "legality": get_signal_types_legality(),
        "accident_history": get_signal_types_accident(),
        "mechanical_issues": get_signal_types_mechanical(),
        "cosmetic_issues": get_signal_types_cosmetic(),
        "mods_performance": get_signal_types_mods_performance(),
        "mods_cosmetic": get_signal_types_mods_cosmetic(),
        "seller_behavior": get_signal_types_seller_behavior(),
    }


# ============================================================================
# Maintenance Enums
# ============================================================================

@lru_cache(maxsize=1)
def get_maintenance_claim_types() -> Set[str]:
    """Get valid maintenance claim types."""
    return get_enum_values("maintenance_claim_type")


@lru_cache(maxsize=1)
def get_evidence_present_types() -> Set[str]:
    """Get valid evidence_present types."""
    return get_enum_values("maintenance_evidence_present")


@lru_cache(maxsize=1)
def get_red_flag_types() -> Set[str]:
    """Get valid maintenance red flag types."""
    return get_enum_values("maintenance_red_flag_type")


# ============================================================================
# Summary Field Enums
# ============================================================================

@lru_cache(maxsize=1)
def get_risk_level_overall_values() -> Set[str]:
    """Get valid risk_level_overall values."""
    return get_enum_values("risk_level_overall")


@lru_cache(maxsize=1)
def get_negotiation_stance_values() -> Set[str]:
    """Get valid negotiation_stance values."""
    return get_enum_values("negotiation_stance")


@lru_cache(maxsize=1)
def get_claimed_condition_values() -> Set[str]:
    """Get valid claimed_condition values."""
    return get_enum_values("claimed_condition")


@lru_cache(maxsize=1)
def get_service_history_level_values() -> Set[str]:
    """Get valid service_history_level values."""
    return get_enum_values("service_history_level")


@lru_cache(maxsize=1)
def get_mods_risk_level_values() -> Set[str]:
    """Get valid mods_risk_level values."""
    return get_enum_values("mods_risk_level")


@lru_cache(maxsize=1)
def get_severity_values() -> Set[str]:
    """Get valid severity values."""
    return get_enum_values("severity")


@lru_cache(maxsize=1)
def get_verification_level_values() -> Set[str]:
    """Get valid verification_level values."""
    return get_enum_values("verification_level")


# ============================================================================
# Other Enums
# ============================================================================

@lru_cache(maxsize=1)
def get_missing_info_types() -> Set[str]:
    """Get valid missing_info types."""
    return get_enum_values("missing_info")


@lru_cache(maxsize=1)
def get_question_priority_values() -> Set[str]:
    """Get valid question priority values."""
    return get_enum_values("question_priority")


# ============================================================================
# Validation Helpers
# ============================================================================

def is_valid_signal_type(signal_type: str, category: str) -> bool:
    """
    Check if a signal type is valid for a given category.
    
    Args:
        signal_type: The signal type to validate
        category: The signal category
        
    Returns:
        True if valid, False otherwise
    """
    all_types = get_all_signal_types()
    valid_types = all_types.get(category, set())
    return signal_type in valid_types


def is_valid_evidence_present(value: str) -> bool:
    """
    Check if an evidence_present value is valid.
    
    Args:
        value: The value to validate
        
    Returns:
        True if valid, False otherwise
    """
    return value in get_evidence_present_types()


def is_valid_severity(value: str) -> bool:
    """
    Check if a severity value is valid.
    
    Args:
        value: The value to validate
        
    Returns:
        True if valid, False otherwise
    """
    return value in get_severity_values()


def is_valid_verification_level(value: str) -> bool:
    """
    Check if a verification_level value is valid.
    
    Args:
        value: The value to validate
        
    Returns:
        True if valid, False otherwise
    """
    return value in get_verification_level_values()


# ============================================================================
# Fallback Values (for when schema can't be loaded)
# ============================================================================

# These are used only if the schema file is missing (shouldn't happen in prod)
FALLBACK_SIGNAL_TYPES = {
    "legality": {
        "no_rego", "rego_expired", "rego_short", "unregistered", "no_rwc",
        "rwc_required", "defected", "inspection_required", "not_roadworthy",
        "non_compliant_mods"
    },
    "accident_history": {
        "writeoff", "repairable_writeoff", "rebuilt_title", "salvage_title",
        "wovr_listed", "accident_damage", "hail_damage", "flood_damage",
        "structural_damage", "airbag_deployed", "chassis_damage",
        "paintwork_repair", "panel_replacement"
    },
    "mechanical_issues": {
        "engine_knock", "engine_misfire", "engine_overheating", "oil_leak",
        "coolant_leak", "head_gasket_suspected", "smoke_from_exhaust",
        "rough_idle", "starting_issue", "gearbox_issue", "clutch_issue",
        "slipping_transmission", "diff_issue", "drivetrain_noise",
        "suspension_issue", "steering_issue", "brake_issue", "tyres_worn",
        "battery_issue", "alternator_issue", "electrical_fault",
        "check_engine_light", "needs_mechanic", "not_running",
        "intermittent_issue", "unknown_mechanical_issue"
    },
    "cosmetic_issues": {
        "scratch", "dent", "paint_fade", "clearcoat_peel", "rust_visible",
        "interior_wear", "cracked_windscreen", "broken_light",
        "missing_parts_cosmetic", "dirty_or_neglected"
    },
    "mods_performance": {
        "tuned", "ecu_tune", "stage_1", "stage_2_or_higher", "turbo_upgrade",
        "turbo_swap", "supercharger", "engine_swap", "e85_flex_fuel",
        "intake_exhaust", "downpipe", "intercooler_upgrade",
        "fuel_system_upgrade", "track_use", "race_build"
    },
    "mods_cosmetic": {
        "aftermarket_wheels", "bodykit", "wrap", "tint", "lowered", "lifted",
        "custom_lights", "interior_custom", "audio_upgrade"
    },
    "seller_behavior": {
        "need_gone", "moving_sale", "urgent_sale", "price_drop_mentioned",
        "firm_price", "open_to_offers", "no_timewasters", "no_lowballers",
        "swap_trade", "cash_only", "deposit_required", "finance_available",
        "delivery_available", "transparent_disclosure", "vague_description",
        "contradictory_claims", "too_good_to_be_true_language"
    },
}

FALLBACK_EVIDENCE_PRESENT = {
    "logbook", "receipts", "workshop_invoice", "photos_of_records", "none"
}
