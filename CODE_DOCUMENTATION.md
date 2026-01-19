# Code Documentation

## Project Structure

```
src/
├── __init__.py                 # Package initialization
├── config.py                   # Configuration and settings
├── common/
│   ├── __init__.py            # Common package exports
│   └── models.py              # Pydantic models and enums
└── stage4/
    ├── __init__.py            # Stage 4 package exports
    ├── runner.py              # Main pipeline orchestrator
    ├── text_prep.py           # Text normalization and preparation
    ├── llm_extractor.py       # OpenAI API integration
    ├── evidence_verifier.py   # Evidence validation
    ├── guardrails.py          # Rule-based signal detection
    ├── merger.py              # Signal merging and deduplication
    ├── derived_fields.py      # Summary field computation
    └── schema_validator.py    # JSON Schema validation
```

---

## Module Documentation

### `src/config.py`

**Purpose:** Centralized configuration management.

**Key Constants:**

```python
# API Configuration
OPENAI_API_KEY                  # From environment variable
DEFAULT_MODEL = "gpt-4o-mini"  # Cost-effective model
DEFAULT_TEMPERATURE = 0.0       # Deterministic outputs

# Token Limits
MAX_INPUT_TOKENS = 4000
MAX_OUTPUT_TOKENS = 2000

# Retry Settings
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0          # Exponential backoff base

# Version Constants
STAGE_VERSION = "v1.0.0"
RULESET_VERSION = "v1.0"

# Paths
STAGE4_SCHEMA_PATH              # Path to JSON Schema
EXTRACTOR_PROMPT_PATH           # Path to LLM prompt template

# Confidence Thresholds
VERIFIED_MIN_CONFIDENCE = 0.90
INFERRED_MIN_CONFIDENCE = 0.40
GUARDRAIL_DEFAULT_CONFIDENCE = 0.95
```

**Functions:**
- `get_openai_api_key()` - Validates and returns API key (raises if missing)

---

### `src/common/models.py`

**Purpose:** Pydantic models and enum definitions matching the Stage 4 schema.

**Key Enums:**

```python
# Global Enums
VerificationLevel       # "verified" | "inferred"
Severity                # "low" | "medium" | "high"
ClaimedCondition        # "excellent" | "good" | "fair" | "needs_work" | "unknown"
ServiceHistoryLevel     # "none" | "partial" | "full" | "unknown"
ModsRiskLevel          # "none" | "low" | "medium" | "high" | "unknown"
NegotiationStance      # "open" | "firm" | "unknown"
RiskLevelOverall       # "low" | "medium" | "high" | "unknown"

# Signal Type Enums
LegalityType           # "defected", "no_rego", "rego_expired", etc.
AccidentHistoryType    # "writeoff", "salvage_title", "flood_damage", etc.
MechanicalIssueType    # "not_running", "overheating", "engine_knock", etc.
ModsPerformanceType    # "stage_2_or_higher", "e85_flex_fuel", "tuned", etc.
# ... (see file for complete list)
```

**Pydantic Models:**

```python
class Signal(BaseModel):
    type: str
    severity: Severity
    verification_level: VerificationLevel
    evidence_text: str
    confidence: float  # [0, 1]

class MaintenanceClaim(BaseModel):
    type: MaintenanceClaimType
    details: Optional[str]
    evidence_text: str
    confidence: float
    verification_level: VerificationLevel

class FollowUpQuestion(BaseModel):
    question: str
    reason: str
    priority: QuestionPriority
    driven_by: List[str]
```

**Usage:** Models provide type safety and can serialize to JSON matching the schema.

---

### `src/stage4/runner.py`

**Purpose:** Main entry point - orchestrates the complete pipeline.

**Main Function:**

```python
def run_stage4(
    listing: Dict[str, Any],
    source_snapshot_id: Optional[str] = None,
    skip_llm: bool = False,
    model: str = DEFAULT_MODEL,
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Run complete Stage 4 pipeline.
    
    Args:
        listing: Must contain 'listing_id', 'title', 'description'
        source_snapshot_id: For idempotency tracking (defaults to listing_id)
        skip_llm: If True, only use guardrails (faster, no API calls)
        model: OpenAI model identifier
        validate: If True, validate output against schema
        
    Returns:
        Complete Stage 4 output dictionary
        
    Raises:
        ValidationError: If validate=True and output invalid
    """
```

**Pipeline Flow:**
1. Extract and validate listing fields
2. Normalize text
3. Run LLM extraction (or fallback)
4. Verify evidence in LLM signals
5. Run guardrail rules
6. Merge LLM + guardrail signals
7. Compute derived fields
8. Build output structure
9. Validate schema (if enabled)

**Helper Functions:**
- `build_output()` - Constructs final output dictionary
- `run_stage4_batch()` - Process multiple listings
- `run_guardrails_only()` - Quick guardrail-only test

---

### `src/stage4/text_prep.py`

**Purpose:** Text normalization and sentence splitting.

**Key Classes:**

```python
@dataclass
class PreparedText:
    original_title: str
    original_description: str
    combined_text: str           # title + description
    normalized_text: str         # lowercase for pattern matching
    sentences: List[str]         # sentence-split for evidence
```

**Functions:**

```python
def normalize_text(title: str, description: str) -> PreparedText:
    """Normalize text, preserving original for evidence matching."""

def split_sentences(text: str) -> List[str]:
    """Split text into sentences for evidence extraction."""

def find_evidence_span(
    pattern: str,
    text: str,
    sentences: List[str],
    window_size: int = 200
) -> Optional[str]:
    """Extract evidence span containing pattern match."""

def check_evidence_exists(evidence_text: str, original_text: str) -> bool:
    """Check if evidence exists verbatim (case-insensitive)."""
```

**Design:** Preserves original text for exact evidence matching while providing normalized versions for pattern matching.

---

### `src/stage4/guardrails.py`

**Purpose:** Deterministic rule-based signal detection.

**Rule Format:**

Each rule is a tuple:
```python
(pattern, signal_type, category, severity)
```

Example:
```python
(r'\bdefect(?:ed)?\b', 'defected', 'legality', 'high')
```

**Rule Categories:**
- `WRITEOFF_SALVAGE_RULES` - Accident history patterns
- `LEGALITY_RULES` - Registration, defects, RWC
- `MECHANICAL_RULES` - Engine, transmission issues
- `PERFORMANCE_MODS_RULES` - Tuning, modifications
- `SELLER_BEHAVIOR_RULES` - Pricing, urgency signals

**Main Function:**

```python
def run_guardrails(prepared_text: PreparedText) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run all guardrail rules against prepared text.
    
    Returns:
        Dictionary with signal categories as keys, lists of signals as values.
        Each signal has:
        - type: signal type enum value
        - severity: "low" | "medium" | "high"
        - verification_level: "verified"
        - evidence_text: exact substring from original text
        - confidence: 0.95 (always)
    """
```

**Properties:**
- All signals have `verification_level="verified"`
- All signals have `confidence=0.95`
- Evidence text is verbatim from source
- Never produces false positives (patterns are strict)

---

### `src/stage4/llm_extractor.py`

**Purpose:** OpenAI API integration for structured extraction.

**Functions:**

```python
def extract_with_llm(
    listing_id: str,
    source_snapshot_id: str,
    title: str,
    description: str,
    vehicle_type: str = "unknown",
    price: Optional[float] = None,
    mileage: Optional[int] = None,
    model: str = DEFAULT_MODEL,
) -> Dict[str, Any]:
    """
    Extract structured intelligence using LLM.
    
    Returns:
        Parsed extraction result (schema-compliant) or fallback on failure.
    """

def call_openai_with_retry(
    prompt: str,
    model: str,
    max_retries: int = MAX_RETRIES,
) -> Optional[str]:
    """
    Call OpenAI API with exponential backoff retry.
    
    Returns:
        Response text or None on failure.
    """

def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM JSON response, handling markdown code blocks.
    
    Raises:
        json.JSONDecodeError: If response is not valid JSON.
    """
```

**Prompt Building:**
- Loads base prompt from `stages/stage4_description_intel/prompts/extractor_prompt.md`
- Injects listing-specific fields (title, description, etc.)
- Requires strict JSON output (no markdown)

**Error Handling:**
- Rate limits → Retry with backoff
- Timeouts → Return None (triggers fallback)
- Invalid JSON → Return fallback structure

---

### `src/stage4/evidence_verifier.py`

**Purpose:** Validate signals have valid evidence text.

**Functions:**

```python
def verify_signals(
    extraction_result: Dict[str, Any],
    original_text: str,
) -> Dict[str, Any]:
    """
    Verify all signals in extraction result.
    
    Rejects signals without valid evidence_text.
    Updates verification_level and confidence based on evidence quality.
    """

def verify_single_signal(
    signal: Dict[str, Any],
    original_text: str,
) -> Optional[Dict[str, Any]]:
    """
    Verify a single signal.
    
    Returns:
        Verified signal (with updated confidence) or None if rejected.
    """

def is_explicit_evidence(evidence_text: str, signal_type: str) -> bool:
    """
    Determine if evidence is explicit (verified) or implicit (inferred).
    
    Explicit: "defected", "write off", "stage 2"
    Implicit: "needs love", "easy fix", "minor issue"
    """
```

**Verification Logic:**
1. Check evidence_text exists in original text (case-insensitive)
2. If not found → Reject signal (return None)
3. If explicit wording → `verification_level="verified"`, confidence ≥ 0.90
4. If implicit wording → `verification_level="inferred"`, confidence < 0.90

**Safety:** Prevents hallucination by requiring verbatim substring matches.

---

### `src/stage4/merger.py`

**Purpose:** Combine LLM and guardrail signals.

**Functions:**

```python
def merge_signals(
    llm_signals: Dict[str, List[Dict[str, Any]]],
    rule_signals: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Merge LLM and rule signals with deduplication.
    
    Strategy:
    - Union both signal sets
    - Deduplicate by (type, evidence_text)
    - Prefer rule confidence on conflicts
    """

def merge_maintenance(
    llm_maintenance: Dict[str, Any],
    rule_signals: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Merge maintenance section from LLM (rules don't detect maintenance).
    """

def get_signal_key(signal: Dict[str, Any]) -> Tuple[str, str]:
    """
    Generate deduplication key: (type, normalized_evidence_text)
    """
```

**Deduplication:**
- Signals with same `type` and `evidence_text` are considered duplicates
- Guardrail signals always win conflicts (higher confidence)
- Maintains original verification levels from both sources

---

### `src/stage4/derived_fields.py`

**Purpose:** Compute summary fields from signals (deterministic rules).

**Main Function:**

```python
def compute_derived_fields(
    signals: Dict[str, List[Dict[str, Any]]],
    maintenance: Dict[str, Any],
    llm_summaries: Dict[str, str],
) -> Dict[str, str]:
    """
    Compute all derived summary fields.
    
    Returns:
        Dictionary with: risk_level_overall, mods_risk_level,
        service_history_level, negotiation_stance, claimed_condition
    """
```

**Computation Functions:**

```python
def compute_risk_level_overall(signals) -> str:
    """
    HIGH: Any HIGH severity verified signal
    MEDIUM: Multiple medium signals or inferred high
    LOW: Only low cosmetic signals
    UNKNOWN: No signals
    """

def compute_mods_risk_level(mods_performance) -> str:
    """
    HIGH: stage 2+, turbo swap, E85, track use
    MEDIUM: tuned, intake/exhaust
    LOW: Cosmetic only
    NONE: No mods
    """

def compute_service_history_level(maintenance) -> str:
    """
    FULL: Logbook + receipts
    PARTIAL: Claims without proof
    NONE: Explicit "no history"
    UNKNOWN: Not mentioned
    """

def compute_negotiation_stance(seller_behavior) -> str:
    """
    FIRM: "firm price", "no lowballers"
    OPEN: "negotiable", "need gone"
    UNKNOWN: Not mentioned
    """
```

**Design:** All computations are deterministic (no randomness) ensuring idempotency.

---

### `src/stage4/schema_validator.py`

**Purpose:** Validate output against JSON Schema contract.

**Functions:**

```python
def validate_stage4_output(output: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate output against schema.
    
    Returns:
        (is_valid, list_of_error_messages)
    """

def validate_or_raise(output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate output, raising ValidationError on failure.
    """

def load_schema() -> Dict:
    """
    Load JSON Schema from file (cached after first load).
    """
```

**Validation Checks:**
- Required fields present
- Enum values match schema
- Confidence in [0, 1]
- Evidence text non-empty
- Nested structures match schema

**Error Messages:** Include field paths for debugging (e.g., `payload.signals.legality[0].confidence`).

---

## API Reference

### Main Entry Point

```python
from stage4.runner import run_stage4

result = run_stage4(
    listing={
        "listing_id": "123",
        "title": "Subaru WRX",
        "description": "Stage 2 tune...",
    },
    skip_llm=True,  # Use guardrails only
    validate=True,  # Validate schema
)
```

### Direct Module Usage

```python
# Text preparation
from stage4.text_prep import normalize_text
prepared = normalize_text(title, description)

# Guardrails
from stage4.guardrails import run_guardrails
signals = run_guardrails(prepared)

# Schema validation
from stage4.schema_validator import validate_stage4_output
is_valid, errors = validate_stage4_output(output)
```

---

## Type Hints

All functions use type hints for IDE support and type checking:

```python
from typing import Dict, List, Optional, Tuple

def example(
    text: str,
    signals: Dict[str, List[Dict[str, Any]]],
    optional_param: Optional[int] = None,
) -> Tuple[bool, List[str]]:
    ...
```

**Note:** Uses `typing` module for Python 3.9 compatibility (not `|` union syntax).

---

## Error Handling Patterns

### LLM Failures

```python
try:
    response = call_openai_with_retry(prompt, model)
except Exception:
    return create_fallback_output(...)
```

### Validation Failures

```python
is_valid, errors = validate_stage4_output(output)
if not is_valid:
    raise ValidationError(f"Schema validation failed: {errors}")
```

### Evidence Failures

```python
verified_signal = verify_single_signal(signal, original_text)
if verified_signal is None:
    # Signal rejected - no valid evidence
    continue
```

---

## Code Style

- **Format:** PEP 8 compliant
- **Docstrings:** Google style
- **Naming:** snake_case for functions/variables, PascalCase for classes
- **Imports:** Absolute imports (e.g., `from stage4.runner import run_stage4`)

---

## Testing

See `TESTING.md` for detailed testing documentation.

---

## Related Documentation

- **Architecture:** See `ARCHITECTURE.md`
- **Testing:** See `TESTING.md`
- **Contributing:** See `CONTRIBUTING.md`
