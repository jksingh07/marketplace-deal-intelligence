"""
Extraction Schema for Structured Outputs

Defines the JSON schema that constrains LLM output to valid structure.
This is used with OpenAI's Structured Outputs feature.
"""

from typing import Dict, Any

# Simplified extraction schema for LLM structured outputs
# This defines ONLY what the LLM extracts - not the full Stage 4 output
EXTRACTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["signals", "maintenance", "summaries"],
    "properties": {
        "signals": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "legality", "accident_history", "mechanical_issues",
                "cosmetic_issues", "mods_performance", "mods_cosmetic",
                "seller_behavior"
            ],
            "properties": {
                "legality": {"$ref": "#/$defs/signal_array_legality"},
                "accident_history": {"$ref": "#/$defs/signal_array_accident"},
                "mechanical_issues": {"$ref": "#/$defs/signal_array_mechanical"},
                "cosmetic_issues": {"$ref": "#/$defs/signal_array_cosmetic"},
                "mods_performance": {"$ref": "#/$defs/signal_array_mods_perf"},
                "mods_cosmetic": {"$ref": "#/$defs/signal_array_mods_cosm"},
                "seller_behavior": {"$ref": "#/$defs/signal_array_seller"},
            }
        },
        "maintenance": {
            "type": "object",
            "additionalProperties": False,
            "required": ["claims", "evidence_present", "red_flags"],
            "properties": {
                "claims": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/maintenance_claim"}
                },
                "evidence_present": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/evidence_present_enum"}
                },
                "red_flags": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/red_flag"}
                }
            }
        },
        "summaries": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "claimed_condition", "service_history_level",
                "mods_risk_level", "negotiation_stance"
            ],
            "properties": {
                "claimed_condition": {
                    "type": "string",
                    "enum": ["excellent", "good", "fair", "needs_work", "unknown"]
                },
                "service_history_level": {
                    "type": "string",
                    "enum": ["none", "partial", "full", "unknown"]
                },
                "mods_risk_level": {
                    "type": "string",
                    "enum": ["none", "low", "medium", "high", "unknown"]
                },
                "negotiation_stance": {
                    "type": "string",
                    "enum": ["open", "firm", "unknown"]
                }
            }
        },
        "missing_info": {
            "type": "array",
            "items": {"$ref": "#/$defs/missing_info_enum"}
        },
        "follow_up_questions": {
            "type": "array",
            "items": {"$ref": "#/$defs/follow_up_question"}
        },
        "extraction_warnings": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "$defs": {
        # Base signal structure
        "signal_base": {
            "type": "object",
            "additionalProperties": False,
            "required": ["type", "severity", "verification_level", "evidence_text", "confidence"],
            "properties": {
                "type": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                "verification_level": {"type": "string", "enum": ["verified", "inferred"]},
                "evidence_text": {"type": "string", "minLength": 1},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            }
        },
        
        # Signal type enums per category
        "signal_legality_type": {
            "type": "string",
            "enum": [
                "no_rego", "rego_expired", "rego_short", "unregistered", "no_rwc",
                "rwc_required", "defected", "inspection_required", "not_roadworthy",
                "non_compliant_mods"
            ]
        },
        "signal_accident_type": {
            "type": "string",
            "enum": [
                "writeoff", "repairable_writeoff", "rebuilt_title", "salvage_title",
                "wovr_listed", "accident_damage", "hail_damage", "flood_damage",
                "structural_damage", "airbag_deployed", "chassis_damage",
                "paintwork_repair", "panel_replacement"
            ]
        },
        "signal_mechanical_type": {
            "type": "string",
            "enum": [
                "engine_knock", "engine_misfire", "engine_overheating", "oil_leak",
                "coolant_leak", "head_gasket_suspected", "smoke_from_exhaust",
                "rough_idle", "starting_issue", "gearbox_issue", "clutch_issue",
                "slipping_transmission", "diff_issue", "drivetrain_noise",
                "suspension_issue", "steering_issue", "brake_issue", "tyres_worn",
                "battery_issue", "alternator_issue", "electrical_fault",
                "check_engine_light", "needs_mechanic", "not_running",
                "intermittent_issue", "unknown_mechanical_issue"
            ]
        },
        "signal_cosmetic_type": {
            "type": "string",
            "enum": [
                "scratch", "dent", "paint_fade", "clearcoat_peel", "rust_visible",
                "interior_wear", "cracked_windscreen", "broken_light",
                "missing_parts_cosmetic", "dirty_or_neglected"
            ]
        },
        "signal_mods_performance_type": {
            "type": "string",
            "enum": [
                "tuned", "ecu_tune", "stage_1", "stage_2_or_higher", "turbo_upgrade",
                "turbo_swap", "supercharger", "engine_swap", "e85_flex_fuel",
                "intake_exhaust", "downpipe", "intercooler_upgrade",
                "fuel_system_upgrade", "track_use", "race_build"
            ]
        },
        "signal_mods_cosmetic_type": {
            "type": "string",
            "enum": [
                "aftermarket_wheels", "bodykit", "wrap", "tint", "lowered", "lifted",
                "custom_lights", "interior_custom", "audio_upgrade"
            ]
        },
        "signal_seller_behavior_type": {
            "type": "string",
            "enum": [
                "need_gone", "moving_sale", "urgent_sale", "price_drop_mentioned",
                "firm_price", "open_to_offers", "no_timewasters", "no_lowballers",
                "swap_trade", "cash_only", "deposit_required", "finance_available",
                "delivery_available", "transparent_disclosure", "vague_description",
                "contradictory_claims", "too_good_to_be_true_language"
            ]
        },
        
        # Signal arrays with typed elements
        "signal_array_legality": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "severity", "verification_level", "evidence_text", "confidence"],
                "properties": {
                    "type": {"$ref": "#/$defs/signal_legality_type"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "verification_level": {"type": "string", "enum": ["verified", "inferred"]},
                    "evidence_text": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "signal_array_accident": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "severity", "verification_level", "evidence_text", "confidence"],
                "properties": {
                    "type": {"$ref": "#/$defs/signal_accident_type"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "verification_level": {"type": "string", "enum": ["verified", "inferred"]},
                    "evidence_text": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "signal_array_mechanical": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "severity", "verification_level", "evidence_text", "confidence"],
                "properties": {
                    "type": {"$ref": "#/$defs/signal_mechanical_type"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "verification_level": {"type": "string", "enum": ["verified", "inferred"]},
                    "evidence_text": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "signal_array_cosmetic": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "severity", "verification_level", "evidence_text", "confidence"],
                "properties": {
                    "type": {"$ref": "#/$defs/signal_cosmetic_type"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "verification_level": {"type": "string", "enum": ["verified", "inferred"]},
                    "evidence_text": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "signal_array_mods_perf": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "severity", "verification_level", "evidence_text", "confidence"],
                "properties": {
                    "type": {"$ref": "#/$defs/signal_mods_performance_type"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "verification_level": {"type": "string", "enum": ["verified", "inferred"]},
                    "evidence_text": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "signal_array_mods_cosm": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "severity", "verification_level", "evidence_text", "confidence"],
                "properties": {
                    "type": {"$ref": "#/$defs/signal_mods_cosmetic_type"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "verification_level": {"type": "string", "enum": ["verified", "inferred"]},
                    "evidence_text": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        "signal_array_seller": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "severity", "verification_level", "evidence_text", "confidence"],
                "properties": {
                    "type": {"$ref": "#/$defs/signal_seller_behavior_type"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "verification_level": {"type": "string", "enum": ["verified", "inferred"]},
                    "evidence_text": {"type": "string", "minLength": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        },
        
        # Maintenance types
        "maintenance_claim_type": {
            "type": "string",
            "enum": [
                "serviced_recently", "regular_service_claimed", "logbook_mentioned",
                "receipts_mentioned", "major_service_done", "timing_belt_done",
                "water_pump_done", "clutch_replaced", "gearbox_rebuilt",
                "engine_rebuilt", "new_tyres", "new_brakes", "battery_replaced"
            ]
        },
        "maintenance_claim": {
            "type": "object",
            "additionalProperties": False,
            "required": ["type", "details", "evidence_text", "confidence", "verification_level"],
            "properties": {
                "type": {"$ref": "#/$defs/maintenance_claim_type"},
                "details": {"type": ["string", "null"]},
                "evidence_text": {"type": "string", "minLength": 1},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "verification_level": {"type": "string", "enum": ["verified", "inferred"]}
            }
        },
        "evidence_present_enum": {
            "type": "string",
            "enum": ["logbook", "receipts", "workshop_invoice", "photos_of_records", "none"]
        },
        "red_flag_type": {
            "type": "string",
            "enum": [
                "claim_without_proof", "major_work_no_receipts",
                "inconsistent_service_story", "recent_issue_disguised_as_minor",
                "odometer_or_history_unclear"
            ]
        },
        "red_flag": {
            "type": "object",
            "additionalProperties": False,
            "required": ["type", "severity", "verification_level", "evidence_text", "confidence"],
            "properties": {
                "type": {"$ref": "#/$defs/red_flag_type"},
                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                "verification_level": {"type": "string", "enum": ["verified", "inferred"]},
                "evidence_text": {"type": "string", "minLength": 1},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}
            }
        },
        
        # Missing info
        "missing_info_enum": {
            "type": "string",
            "enum": [
                "vin_unknown", "ppsr_or_finance_status_unknown", "rego_expiry_unknown",
                "rwc_status_unknown", "accident_history_unknown", "service_history_unknown",
                "number_of_owners_unknown", "reason_for_selling_unknown",
                "recent_repairs_proof_unknown", "mods_engineered_unknown",
                "inspection_availability_unknown"
            ]
        },
        
        # Follow-up questions
        "follow_up_question": {
            "type": "object",
            "additionalProperties": False,
            "required": ["question", "reason", "priority", "driven_by"],
            "properties": {
                "question": {"type": "string", "minLength": 5},
                "reason": {"type": "string", "minLength": 3},
                "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                "driven_by": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    }
}


def get_extraction_schema_for_openai() -> Dict[str, Any]:
    """
    Get the extraction schema formatted for OpenAI Structured Outputs.
    
    OpenAI's structured outputs requires a specific format without $ref.
    This function returns a flattened schema.
    
    Returns:
        Schema dict ready for OpenAI API
    """
    # For OpenAI structured outputs, we need to inline the $refs
    # This is a simplified version that works with the API
    return {
        "name": "stage4_extraction",
        "strict": True,
        "schema": _flatten_schema(EXTRACTION_SCHEMA)
    }


def _flatten_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten a schema by resolving $ref references.
    
    OpenAI Structured Outputs doesn't support $ref, so we inline definitions.
    """
    defs = schema.get("$defs", {})
    
    def resolve_refs(obj: Any) -> Any:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_path = obj["$ref"]
                # Parse reference like "#/$defs/signal_legality_type"
                if ref_path.startswith("#/$defs/"):
                    def_name = ref_path.split("/")[-1]
                    if def_name in defs:
                        return resolve_refs(defs[def_name])
                return obj
            return {k: resolve_refs(v) for k, v in obj.items() if k != "$defs"}
        elif isinstance(obj, list):
            return [resolve_refs(item) for item in obj]
        return obj
    
    result = resolve_refs(schema)
    return result
