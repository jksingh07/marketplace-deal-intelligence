"""
LLM Extractor Module for Stage 4

Handles OpenAI API calls for structured extraction from listing text.
Uses OpenAI Structured Outputs for schema-constrained responses.
"""

import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Dict, List, Tuple
from dataclasses import dataclass

from openai import OpenAI, APIError, APITimeoutError, RateLimitError

from config import (
    get_openai_api_key,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_OUTPUT_TOKENS,
    OPENAI_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY_BASE,
    STAGE_VERSION,
    RULESET_VERSION,
    EXTRACTOR_PROMPT_PATH,
)
from stage4.extraction_schema import get_extraction_schema_for_openai

# Configure logging
logger = logging.getLogger(__name__)


def load_extractor_prompt() -> str:
    """Load the extractor prompt template from file."""
    prompt_path = EXTRACTOR_PROMPT_PATH
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Extractor prompt not found at {prompt_path}")
    
    return prompt_path.read_text()


def build_extraction_prompt(
    listing_id: str,
    title: str,
    description: str,
    vehicle_type: str = "unknown",
    price: Optional[float] = None,
    mileage: Optional[int] = None,
) -> str:
    """
    Build the complete prompt for LLM extraction.
    
    Args:
        listing_id: Unique listing identifier
        title: Listing title
        description: Listing description
        vehicle_type: Type of vehicle (car/bike/unknown)
        price: Asking price (optional)
        mileage: Odometer reading (optional)
        
    Returns:
        Complete prompt string
    """
    # Load base prompt
    base_prompt = load_extractor_prompt()
    
    # Build input section
    input_section = f"""
## Input for This Extraction

- **listing_id**: {listing_id}
- **title**: {title}
- **description**: {description}
- **vehicle_type**: {vehicle_type}
- **price**: {price if price is not None else "not provided"}
- **mileage**: {mileage if mileage is not None else "not provided"}

Now extract the structured intelligence following the schema.
You MUST return valid JSON matching the extraction schema.
"""
    
    return base_prompt + "\n---\n" + input_section


@dataclass
class TokenUsage:
    """Token usage details from an API call."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str


def extract_with_llm(
    listing_id: str,
    source_snapshot_id: str,
    title: str,
    description: str,
    vehicle_type: str = "unknown",
    price: Optional[float] = None,
    mileage: Optional[int] = None,
    model: str = DEFAULT_MODEL,
    use_structured_output: bool = True,
) -> Tuple[Dict[str, Any], Optional[TokenUsage]]:
    """
    Extract structured intelligence from listing using LLM.
    
    Args:
        listing_id: Unique listing identifier
        source_snapshot_id: Snapshot identifier for idempotency
        title: Listing title
        description: Listing description
        vehicle_type: Type of vehicle
        price: Asking price
        mileage: Odometer reading
        model: OpenAI model to use
        use_structured_output: Whether to use OpenAI Structured Outputs
        
    Returns:
        Tuple of (parsed extraction result or fallback structure on failure, total tokens used or None)
    """
    logger.info(f"Starting LLM extraction for listing {listing_id}")
    start_time = time.time()
    
    # Build prompt
    prompt = build_extraction_prompt(
        listing_id=listing_id,
        title=title,
        description=description,
        vehicle_type=vehicle_type,
        price=price,
        mileage=mileage,
    )
    
    # Call OpenAI with retries
    extraction_result, token_usage = call_openai_with_retry(
        prompt=prompt,
        model=model,
        use_structured_output=use_structured_output,
    )
    
    elapsed = time.time() - start_time
    logger.info(f"LLM extraction completed in {elapsed:.2f}s for listing {listing_id}")
    
    if extraction_result is None:
        logger.warning(f"LLM extraction failed for listing {listing_id}")
        # LLM failed, return minimal fallback
        return create_fallback_output(
            listing_id=listing_id,
            source_snapshot_id=source_snapshot_id,
            title=title,
            description=description,
            warning="LLM extraction failed after retries",
        ), None
    
    # Build full output structure from extraction
    try:
        result = build_llm_output(
            extraction=extraction_result,
            listing_id=listing_id,
            source_snapshot_id=source_snapshot_id,
            title=title,
            description=description,
            model=model,
        )
        return result, token_usage
        
    except Exception as e:
        logger.error(f"Error building output for listing {listing_id}: {e}")
        return create_fallback_output(
            listing_id=listing_id,
            source_snapshot_id=source_snapshot_id,
            title=title,
            description=description,
            warning=f"Error processing LLM output: {str(e)}",
        ), None


def call_openai_with_retry(
    prompt: str,
    model: str,
    max_retries: int = MAX_RETRIES,
    use_structured_output: bool = True,
) -> Tuple[Optional[Dict[str, Any]], Optional[TokenUsage]]:
    """
    Call OpenAI API with exponential backoff retry.
    
    Uses Structured Outputs when available for schema-constrained responses.
    
    Args:
        prompt: Complete prompt to send
        model: Model to use
        max_retries: Maximum retry attempts
        use_structured_output: Whether to use JSON schema mode
        
    Returns:
        Tuple of (parsed response dict or None on failure, total tokens used or None)
    """
    client = OpenAI(api_key=get_openai_api_key())
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"OpenAI API call attempt {attempt + 1}/{max_retries}")
            
            # Build request parameters
            request_params = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a precise JSON extraction assistant for vehicle listings. "
                            "Extract signals, maintenance info, and summaries from the listing text. "
                            "Only include signals with verbatim evidence from the text. "
                            "Output valid JSON matching the schema."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": DEFAULT_TEMPERATURE,
                "max_tokens": MAX_OUTPUT_TOKENS,
                "timeout": OPENAI_TIMEOUT,
            }
            
            # Add structured output format if enabled
            if use_structured_output:
                request_params["response_format"] = {
                    "type": "json_object"
                }
            
            response = client.chat.completions.create(**request_params)
            
            response_text = response.choices[0].message.content
            
            # Extract and log token usage
            token_usage = None
            if response.usage:
                token_usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    model=model
                )
                logger.info(
                    f"Token usage: prompt={token_usage.prompt_tokens}, "
                    f"completion={token_usage.completion_tokens}, "
                    f"total={token_usage.total_tokens}, model={model}"
                )
            
            # Parse response
            parsed_response = parse_llm_response(response_text)
            return parsed_response, token_usage
            
        except RateLimitError as e:
            logger.warning(f"Rate limit error: {e}")
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error("Max retries exceeded due to rate limiting")
                return None, None
                
        except (APIError, APITimeoutError) as e:
            logger.warning(f"API error: {e}")
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"Max retries exceeded: {e}")
                return None, None
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                time.sleep(delay)
            else:
                return None, None
                
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None, None
    
    return None, None


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM response text into JSON.
    
    Handles common issues like markdown code blocks.
    
    Args:
        response_text: Raw response from LLM
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        json.JSONDecodeError: If response is not valid JSON
    """
    text = response_text.strip()
    
    # Remove markdown code blocks if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```)
        lines = lines[1:]
        # Remove last line if it's ```)
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    
    return json.loads(text)


def build_llm_output(
    extraction: Dict[str, Any],
    listing_id: str,
    source_snapshot_id: str,
    title: str,
    description: str,
    model: str,
) -> Dict[str, Any]:
    """
    Build the full Stage 4 output structure from LLM extraction.
    
    Args:
        extraction: Raw extraction result from LLM
        listing_id: Listing identifier
        source_snapshot_id: Snapshot identifier
        title: Original title
        description: Original description
        model: Model used
        
    Returns:
        Full Stage 4 output structure
    """
    # Get signals from extraction (handle both old and new formats)
    signals = extraction.get("signals", {})
    if not signals:
        # Try payload format from old prompt
        payload = extraction.get("payload", {})
        signals = payload.get("signals", {})
    
    # Ensure all signal categories exist
    for category in ["legality", "accident_history", "mechanical_issues",
                     "cosmetic_issues", "mods_performance", "mods_cosmetic",
                     "seller_behavior"]:
        if category not in signals:
            signals[category] = []
    
    # Get maintenance from extraction
    maintenance = extraction.get("maintenance", {})
    if not maintenance:
        payload = extraction.get("payload", {})
        maintenance = payload.get("maintenance", {})
    
    # Ensure maintenance has all required fields
    if "claims" not in maintenance:
        maintenance["claims"] = []
    if "evidence_present" not in maintenance:
        maintenance["evidence_present"] = []
    if "red_flags" not in maintenance:
        maintenance["red_flags"] = []
    
    # Get summaries
    summaries = extraction.get("summaries", {})
    if not summaries:
        # Try to get from payload or top level
        payload = extraction.get("payload", extraction)
        summaries = {
            "claimed_condition": payload.get("claimed_condition", "unknown"),
            "service_history_level": payload.get("service_history_level", "unknown"),
            "mods_risk_level": payload.get("mods_risk_level", "unknown"),
            "negotiation_stance": payload.get("negotiation_stance", "unknown"),
        }
    
    # Get other fields
    missing_info = extraction.get("missing_info", [])
    if not missing_info:
        missing_info = extraction.get("payload", {}).get("missing_info", [])
    
    follow_up = extraction.get("follow_up_questions", [])
    if not follow_up:
        follow_up = extraction.get("payload", {}).get("follow_up_questions", [])
    
    warnings = extraction.get("extraction_warnings", [])
    if not warnings:
        warnings = extraction.get("payload", {}).get("extraction_warnings", [])
    
    return {
        "listing_id": listing_id,
        "source_snapshot_id": source_snapshot_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stage_name": "stage4_description_intelligence",
        "stage_version": STAGE_VERSION,
        "ruleset_version": RULESET_VERSION,
        "llm_version": model,
        "payload": {
            "risk_level_overall": "unknown",  # Computed later by derived_fields
            "negotiation_stance": summaries.get("negotiation_stance", "unknown"),
            "claimed_condition": summaries.get("claimed_condition", "unknown"),
            "service_history_level": summaries.get("service_history_level", "unknown"),
            "mods_risk_level": summaries.get("mods_risk_level", "unknown"),
            "signals": signals,
            "maintenance": maintenance,
            "missing_info": missing_info,
            "follow_up_questions": follow_up,
            "extraction_warnings": warnings,
            "source_text_stats": {
                "title_length": len(title),
                "description_length": len(description),
                "contains_keywords_high_risk": False,  # Set by runner
            },
        },
    }


def create_fallback_output(
    listing_id: str,
    source_snapshot_id: str,
    title: str,
    description: str,
    warning: str,
) -> Dict[str, Any]:
    """
    Create a minimal valid output when LLM fails.
    
    This allows the pipeline to continue with rules-only extraction.
    
    Args:
        listing_id: Listing identifier
        source_snapshot_id: Snapshot identifier
        title: Listing title
        description: Listing description
        warning: Warning message to include
        
    Returns:
        Minimal schema-valid output structure
    """
    logger.warning(f"Creating fallback output for {listing_id}: {warning}")
    
    return {
        "listing_id": listing_id,
        "source_snapshot_id": source_snapshot_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "stage_name": "stage4_description_intelligence",
        "stage_version": STAGE_VERSION,
        "ruleset_version": RULESET_VERSION,
        "llm_version": None,
        "payload": {
            "risk_level_overall": "unknown",
            "negotiation_stance": "unknown",
            "claimed_condition": "unknown",
            "service_history_level": "unknown",
            "mods_risk_level": "unknown",
            "signals": {
                "legality": [],
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
            "missing_info": [],
            "follow_up_questions": [],
            "extraction_warnings": [warning],
            "source_text_stats": {
                "title_length": len(title),
                "description_length": len(description),
                "contains_keywords_high_risk": False,
            },
        },
    }
