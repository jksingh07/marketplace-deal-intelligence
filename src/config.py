"""
Configuration for Stage 4 Pipeline

Loads settings from environment variables and provides constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present (try project root and current directory)
# Find project root (src/ directory is one level down from project root)
_project_root = Path(__file__).parent.parent
_env_path = _project_root / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    # Fallback to default behavior (searches current directory and parents)
    load_dotenv()

# ============================================================================
# API Configuration
# ============================================================================

def get_openai_api_key() -> str:
    """Get OpenAI API key, raising if not set.
    
    Reads from environment variable (set directly or loaded from .env file).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Set it in your environment or create a .env file in the project root."
        )
    return api_key

# ============================================================================
# Model Settings
# ============================================================================

# Default model for extraction (cost-effective, sufficient for structured extraction)
DEFAULT_MODEL = "gpt-4o-mini"

# Temperature 0 for deterministic outputs
DEFAULT_TEMPERATURE = 0.0

# Token limits
MAX_INPUT_TOKENS = 4000
MAX_OUTPUT_TOKENS = 2000

# Timeout in seconds
OPENAI_TIMEOUT = 30

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0  # Exponential backoff base

# ============================================================================
# Version Constants
# ============================================================================

STAGE_VERSION = "v1.0.0"
RULESET_VERSION = "v1.0"
EVIDENCE_POLICY_VERSION = "v1.0"

# ============================================================================
# Paths
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
PROMPTS_DIR = PROJECT_ROOT / "stages" / "stage4_description_intel" / "prompts"
DATA_SAMPLES_DIR = PROJECT_ROOT / "data_samples"

# Schema path
STAGE4_SCHEMA_PATH = CONTRACTS_DIR / "stage4_description_intel.schema.json"

# Prompt path
EXTRACTOR_PROMPT_PATH = PROMPTS_DIR / "extractor_prompt.md"

# ============================================================================
# Stage 4 Specific Settings
# ============================================================================

# Confidence thresholds
VERIFIED_MIN_CONFIDENCE = 0.90
INFERRED_MIN_CONFIDENCE = 0.40
GUARDRAIL_DEFAULT_CONFIDENCE = 0.95

# Evidence window size (characters) when full sentence not extractable
EVIDENCE_WINDOW_SIZE = 200

# Minimum description length to consider "short"
SHORT_DESCRIPTION_THRESHOLD = 30
