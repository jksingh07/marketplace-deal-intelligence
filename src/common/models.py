"""
Pydantic models for Stage 4 Description Intelligence.

These models match the enums and structures defined in:
- docs/STAGE_4_SIGNAL_ENUMS.md
- contracts/stage4_description_intel.schema.json
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Global Enums
# ============================================================================

class VerificationLevel(str, Enum):
    """How strongly a signal is supported by text evidence."""
    VERIFIED = "verified"
    INFERRED = "inferred"


class Severity(str, Enum):
    """Impact level of a signal."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ClaimedCondition(str, Enum):
    """Seller-stated vehicle condition."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    NEEDS_WORK = "needs_work"
    UNKNOWN = "unknown"


class ServiceHistoryLevel(str, Enum):
    """Level of service history documentation."""
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"
    UNKNOWN = "unknown"


class ModsRiskLevel(str, Enum):
    """Risk level of modifications."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class NegotiationStance(str, Enum):
    """Seller's negotiation stance."""
    OPEN = "open"
    FIRM = "firm"
    UNKNOWN = "unknown"


class RiskLevelOverall(str, Enum):
    """Overall risk level (derived, not LLM-decided)."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


# ============================================================================
# Signal Type Enums
# ============================================================================

class LegalityType(str, Enum):
    """Legality signal types."""
    NO_REGO = "no_rego"
    REGO_EXPIRED = "rego_expired"
    REGO_SHORT = "rego_short"
    UNREGISTERED = "unregistered"
    NO_RWC = "no_rwc"
    RWC_REQUIRED = "rwc_required"
    DEFECTED = "defected"
    INSPECTION_REQUIRED = "inspection_required"
    NOT_ROADWORTHY = "not_roadworthy"
    NON_COMPLIANT_MODS = "non_compliant_mods"


class AccidentHistoryType(str, Enum):
    """Accident history signal types."""
    WRITEOFF = "writeoff"
    REPAIRABLE_WRITEOFF = "repairable_writeoff"
    REBUILT_TITLE = "rebuilt_title"
    SALVAGE_TITLE = "salvage_title"
    WOVR_LISTED = "wovr_listed"
    ACCIDENT_DAMAGE = "accident_damage"
    HAIL_DAMAGE = "hail_damage"
    FLOOD_DAMAGE = "flood_damage"
    STRUCTURAL_DAMAGE = "structural_damage"
    AIRBAG_DEPLOYED = "airbag_deployed"
    CHASSIS_DAMAGE = "chassis_damage"
    PAINTWORK_REPAIR = "paintwork_repair"
    PANEL_REPLACEMENT = "panel_replacement"


class MechanicalIssueType(str, Enum):
    """Mechanical issue signal types."""
    ENGINE_KNOCK = "engine_knock"
    ENGINE_MISFIRE = "engine_misfire"
    ENGINE_OVERHEATING = "engine_overheating"
    OIL_LEAK = "oil_leak"
    COOLANT_LEAK = "coolant_leak"
    HEAD_GASKET_SUSPECTED = "head_gasket_suspected"
    SMOKE_FROM_EXHAUST = "smoke_from_exhaust"
    ROUGH_IDLE = "rough_idle"
    STARTING_ISSUE = "starting_issue"
    GEARBOX_ISSUE = "gearbox_issue"
    CLUTCH_ISSUE = "clutch_issue"
    SLIPPING_TRANSMISSION = "slipping_transmission"
    DIFF_ISSUE = "diff_issue"
    DRIVETRAIN_NOISE = "drivetrain_noise"
    SUSPENSION_ISSUE = "suspension_issue"
    STEERING_ISSUE = "steering_issue"
    BRAKE_ISSUE = "brake_issue"
    TYRES_WORN = "tyres_worn"
    BATTERY_ISSUE = "battery_issue"
    ALTERNATOR_ISSUE = "alternator_issue"
    ELECTRICAL_FAULT = "electrical_fault"
    CHECK_ENGINE_LIGHT = "check_engine_light"
    NEEDS_MECHANIC = "needs_mechanic"
    NOT_RUNNING = "not_running"
    INTERMITTENT_ISSUE = "intermittent_issue"
    UNKNOWN_MECHANICAL_ISSUE = "unknown_mechanical_issue"


class CosmeticIssueType(str, Enum):
    """Cosmetic issue signal types."""
    SCRATCH = "scratch"
    DENT = "dent"
    PAINT_FADE = "paint_fade"
    CLEARCOAT_PEEL = "clearcoat_peel"
    RUST_VISIBLE = "rust_visible"
    INTERIOR_WEAR = "interior_wear"
    CRACKED_WINDSCREEN = "cracked_windscreen"
    BROKEN_LIGHT = "broken_light"
    MISSING_PARTS_COSMETIC = "missing_parts_cosmetic"
    DIRTY_OR_NEGLECTED = "dirty_or_neglected"


class ModsPerformanceType(str, Enum):
    """Performance modification signal types."""
    TUNED = "tuned"
    ECU_TUNE = "ecu_tune"
    STAGE_1 = "stage_1"
    STAGE_2_OR_HIGHER = "stage_2_or_higher"
    TURBO_UPGRADE = "turbo_upgrade"
    TURBO_SWAP = "turbo_swap"
    SUPERCHARGER = "supercharger"
    ENGINE_SWAP = "engine_swap"
    E85_FLEX_FUEL = "e85_flex_fuel"
    INTAKE_EXHAUST = "intake_exhaust"
    DOWNPIPE = "downpipe"
    INTERCOOLER_UPGRADE = "intercooler_upgrade"
    FUEL_SYSTEM_UPGRADE = "fuel_system_upgrade"
    TRACK_USE = "track_use"
    RACE_BUILD = "race_build"


class ModsCosmeticType(str, Enum):
    """Cosmetic modification signal types."""
    AFTERMARKET_WHEELS = "aftermarket_wheels"
    BODYKIT = "bodykit"
    WRAP = "wrap"
    TINT = "tint"
    LOWERED = "lowered"
    LIFTED = "lifted"
    CUSTOM_LIGHTS = "custom_lights"
    INTERIOR_CUSTOM = "interior_custom"
    AUDIO_UPGRADE = "audio_upgrade"


class SellerBehaviorType(str, Enum):
    """Seller behavior signal types."""
    NEED_GONE = "need_gone"
    MOVING_SALE = "moving_sale"
    URGENT_SALE = "urgent_sale"
    PRICE_DROP_MENTIONED = "price_drop_mentioned"
    FIRM_PRICE = "firm_price"
    OPEN_TO_OFFERS = "open_to_offers"
    NO_TIMEWASTERS = "no_timewasters"
    NO_LOWBALLERS = "no_lowballers"
    SWAP_TRADE = "swap_trade"
    CASH_ONLY = "cash_only"
    DEPOSIT_REQUIRED = "deposit_required"
    FINANCE_AVAILABLE = "finance_available"
    DELIVERY_AVAILABLE = "delivery_available"
    TRANSPARENT_DISCLOSURE = "transparent_disclosure"
    VAGUE_DESCRIPTION = "vague_description"
    CONTRADICTORY_CLAIMS = "contradictory_claims"
    TOO_GOOD_TO_BE_TRUE_LANGUAGE = "too_good_to_be_true_language"


class MaintenanceClaimType(str, Enum):
    """Maintenance claim types."""
    SERVICED_RECENTLY = "serviced_recently"
    REGULAR_SERVICE_CLAIMED = "regular_service_claimed"
    LOGBOOK_MENTIONED = "logbook_mentioned"
    RECEIPTS_MENTIONED = "receipts_mentioned"
    MAJOR_SERVICE_DONE = "major_service_done"
    TIMING_BELT_DONE = "timing_belt_done"
    WATER_PUMP_DONE = "water_pump_done"
    CLUTCH_REPLACED = "clutch_replaced"
    GEARBOX_REBUILT = "gearbox_rebuilt"
    ENGINE_REBUILT = "engine_rebuilt"
    NEW_TYRES = "new_tyres"
    NEW_BRAKES = "new_brakes"
    BATTERY_REPLACED = "battery_replaced"


class MaintenanceEvidencePresent(str, Enum):
    """Types of maintenance evidence present."""
    LOGBOOK = "logbook"
    RECEIPTS = "receipts"
    WORKSHOP_INVOICE = "workshop_invoice"
    PHOTOS_OF_RECORDS = "photos_of_records"
    NONE = "none"


class MaintenanceRedFlagType(str, Enum):
    """Maintenance red flag types."""
    CLAIM_WITHOUT_PROOF = "claim_without_proof"
    MAJOR_WORK_NO_RECEIPTS = "major_work_no_receipts"
    INCONSISTENT_SERVICE_STORY = "inconsistent_service_story"
    RECENT_ISSUE_DISGUISED_AS_MINOR = "recent_issue_disguised_as_minor"
    ODOMETER_OR_HISTORY_UNCLEAR = "odometer_or_history_unclear"


class MissingInfoType(str, Enum):
    """Missing information types."""
    VIN_UNKNOWN = "vin_unknown"
    PPSR_OR_FINANCE_STATUS_UNKNOWN = "ppsr_or_finance_status_unknown"
    REGO_EXPIRY_UNKNOWN = "rego_expiry_unknown"
    RWC_STATUS_UNKNOWN = "rwc_status_unknown"
    ACCIDENT_HISTORY_UNKNOWN = "accident_history_unknown"
    SERVICE_HISTORY_UNKNOWN = "service_history_unknown"
    NUMBER_OF_OWNERS_UNKNOWN = "number_of_owners_unknown"
    REASON_FOR_SELLING_UNKNOWN = "reason_for_selling_unknown"
    RECENT_REPAIRS_PROOF_UNKNOWN = "recent_repairs_proof_unknown"
    MODS_ENGINEERED_UNKNOWN = "mods_engineered_unknown"
    INSPECTION_AVAILABILITY_UNKNOWN = "inspection_availability_unknown"


class QuestionPriority(str, Enum):
    """Priority level for follow-up questions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================================
# Signal Models
# ============================================================================

class Signal(BaseModel):
    """Base signal model with evidence and confidence."""
    type: str
    severity: Severity
    verification_level: VerificationLevel
    evidence_text: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "severity": self.severity.value,
            "verification_level": self.verification_level.value,
            "evidence_text": self.evidence_text,
            "confidence": self.confidence,
        }


class MaintenanceClaim(BaseModel):
    """Maintenance claim with evidence."""
    type: MaintenanceClaimType
    details: Optional[str] = None
    evidence_text: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    verification_level: VerificationLevel

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "details": self.details,
            "evidence_text": self.evidence_text,
            "confidence": self.confidence,
            "verification_level": self.verification_level.value,
        }


class MaintenanceRedFlag(BaseModel):
    """Maintenance red flag with evidence."""
    type: MaintenanceRedFlagType
    severity: Severity
    verification_level: VerificationLevel
    evidence_text: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "verification_level": self.verification_level.value,
            "evidence_text": self.evidence_text,
            "confidence": self.confidence,
        }


class FollowUpQuestion(BaseModel):
    """Follow-up question for the buyer to ask."""
    question: str = Field(..., min_length=5)
    reason: str = Field(..., min_length=3)
    priority: QuestionPriority
    driven_by: List[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "question": self.question,
            "reason": self.reason,
            "priority": self.priority.value,
            "driven_by": self.driven_by,
        }
