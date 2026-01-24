"""
LLM Pricer Module for Stage 7
Uses OpenAI to estimate market price for a vehicle based on its details.
"""

import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

from openai import OpenAI
from config import (
    get_openai_api_key,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_OUTPUT_TOKENS,
    OPENAI_TIMEOUT,
)

# Configure logging
logger = logging.getLogger(__name__)

def estimate_price_with_llm(
    listing: Dict[str, Any],
    model: str = DEFAULT_MODEL
) -> Dict[str, Any]:
    """
    Estimate market price using LLM knowledge.
    
    Args:
        listing: Listing dictionary containing title, description, price, mileage, etc.
        model: OpenAI model to use
        
    Returns:
        Dictionary with estimated price data (p50, confidence, reasoning)
    """
    client = OpenAI(api_key=get_openai_api_key())
    
    # Extract details
    title = listing.get("title", "")
    description = listing.get("description", "")
    price = listing.get("price")
    mileage = listing.get("mileage")
    vehicle_type = listing.get("vehicle_type", "car")
    
    # Build Prompt
    prompt = f"""
    You are an expert vehicle appraiser. I need you to estimate the current fair market value (Private Party) for the following vehicle.
    
    ## Vehicle Details
    - Title: {title}
    - Description: {description}
    - Listed Price: {price if price else "Not provided"}
    - Mileage: {mileage if mileage else "Not provided"}
    - Type: {vehicle_type}
    
    ## Task
    1. Identify the Year, Make, Model, and Trim from the text.
    2. Estimate the fair market value range for this specific vehicle condition and mileage.
    3. Provide a single point estimate (P50) for the fair market value.
    4. Provide a confidence score (0.0 - 1.0) based on how much info is available and how standard the vehicle is.
    5. Explain your reasoning briefly.
    
    ## Output Format
    You MUST return valid JSON with the following structure:
    {{
        "estimated_market_price_p50": <number>,
        "estimated_market_price_p25": <number>,
        "estimated_market_price_p75": <number>,
        "confidence": <number between 0 and 1>,
        "reasoning": "<string explanation>",
        "comps_used_count": <number, estimate how many similar listings exist in the market generally, e.g. 10, 50, 100>
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful and precise vehicle appraiser."},
                {"role": "user", "content": prompt}
            ],
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=MAX_OUTPUT_TOKENS,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Add metadata
        result["source"] = "llm_estimation"
        result["model_used"] = model
        
        return result
        
    except Exception as e:
        logger.error(f"LLM Pricing failed: {e}")
        # Return fallback
        return {
            "estimated_market_price_p50": price if price else 0,
            "confidence": 0.1,
            "reasoning": f"LLM estimation failed: {str(e)}",
            "comps_used_count": 0,
            "error": str(e)
        }
