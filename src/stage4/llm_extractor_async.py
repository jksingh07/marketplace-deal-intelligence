"""
Async LLM Extractor Module for Stage 4

Provides async/await API for LLM extraction to support concurrent processing.
Uses httpx for async HTTP calls instead of blocking requests.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional, Dict, List

import httpx
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError

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
)
from stage4.llm_extractor import (
    build_extraction_prompt,
    parse_llm_response,
    build_llm_output,
    create_fallback_output,
)

# Configure logging
logger = logging.getLogger(__name__)


async def extract_with_llm_async(
    listing_id: str,
    source_snapshot_id: str,
    title: str,
    description: str,
    vehicle_type: str = "unknown",
    price: Optional[float] = None,
    mileage: Optional[int] = None,
    model: str = DEFAULT_MODEL,
    use_structured_output: bool = True,
) -> Dict[str, Any]:
    """
    Extract structured intelligence from listing using LLM (async version).
    
    Args:
        listing_id: Unique listing identifier
        source_snapshot_id: Snapshot identifier for idempotency
        title: Listing title
        description: Listing description
        vehicle_type: Type of vehicle
        price: Asking price
        mileage: Odometer reading
        model: OpenAI model to use
        use_structured_output: Whether to use JSON mode
        
    Returns:
        Parsed extraction result or fallback structure on failure
    """
    logger.info(f"Starting async LLM extraction for listing {listing_id}")
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
    extraction_result = await call_openai_async(
        prompt=prompt,
        model=model,
        use_structured_output=use_structured_output,
    )
    
    elapsed = time.time() - start_time
    logger.info(f"Async LLM extraction completed in {elapsed:.2f}s for listing {listing_id}")
    
    if extraction_result is None:
        logger.warning(f"Async LLM extraction failed for listing {listing_id}")
        return create_fallback_output(
            listing_id=listing_id,
            source_snapshot_id=source_snapshot_id,
            title=title,
            description=description,
            warning="LLM extraction failed after retries",
        )
    
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
        return result
        
    except Exception as e:
        logger.error(f"Error building output for listing {listing_id}: {e}")
        return create_fallback_output(
            listing_id=listing_id,
            source_snapshot_id=source_snapshot_id,
            title=title,
            description=description,
            warning=f"Error processing LLM output: {str(e)}",
        )


async def call_openai_async(
    prompt: str,
    model: str,
    max_retries: int = MAX_RETRIES,
    use_structured_output: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Call OpenAI API asynchronously with exponential backoff retry.
    
    Args:
        prompt: Complete prompt to send
        model: Model to use
        max_retries: Maximum retry attempts
        use_structured_output: Whether to use JSON mode
        
    Returns:
        Parsed response dict or None on failure
    """
    client = AsyncOpenAI(api_key=get_openai_api_key())
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Async OpenAI API call attempt {attempt + 1}/{max_retries}")
            
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
            
            if use_structured_output:
                request_params["response_format"] = {"type": "json_object"}
            
            response = await client.chat.completions.create(**request_params)
            
            response_text = response.choices[0].message.content
            
            # Log token usage
            if response.usage:
                logger.info(
                    f"Token usage: prompt={response.usage.prompt_tokens}, "
                    f"completion={response.usage.completion_tokens}"
                )
            
            return parse_llm_response(response_text)
            
        except RateLimitError as e:
            logger.warning(f"Rate limit error: {e}")
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.error("Max retries exceeded due to rate limiting")
                return None
                
        except (APIError, APITimeoutError) as e:
            logger.warning(f"API error: {e}")
            if attempt < max_retries - 1:
                delay = RETRY_DELAY_BASE * (2 ** attempt)
                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Max retries exceeded: {e}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(RETRY_DELAY_BASE)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    return None


async def extract_batch_async(
    listings: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
    max_concurrent: int = 5,
) -> List[Dict[str, Any]]:
    """
    Extract from multiple listings concurrently.
    
    Args:
        listings: List of listing dictionaries
        model: OpenAI model to use
        max_concurrent: Maximum concurrent requests
        
    Returns:
        List of extraction results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def extract_with_semaphore(listing: Dict[str, Any]) -> Dict[str, Any]:
        async with semaphore:
            return await extract_with_llm_async(
                listing_id=str(listing.get("listing_id", "unknown")),
                source_snapshot_id=str(listing.get("listing_id", "unknown")),
                title=listing.get("title", ""),
                description=listing.get("description", ""),
                vehicle_type=listing.get("vehicle_type", "unknown"),
                price=listing.get("price"),
                mileage=listing.get("mileage"),
                model=model,
            )
    
    logger.info(f"Starting async batch extraction of {len(listings)} listings")
    start_time = time.time()
    
    tasks = [extract_with_semaphore(listing) for listing in listings]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Batch item {i} failed: {result}")
            listing = listings[i]
            processed_results.append(
                create_fallback_output(
                    listing_id=str(listing.get("listing_id", f"batch_{i}")),
                    source_snapshot_id=str(listing.get("listing_id", f"batch_{i}")),
                    title=listing.get("title", ""),
                    description=listing.get("description", ""),
                    warning=f"Extraction error: {str(result)}",
                )
            )
        else:
            processed_results.append(result)
    
    elapsed = time.time() - start_time
    logger.info(
        f"Async batch extraction completed: {len(listings)} listings in {elapsed:.2f}s "
        f"({elapsed/len(listings):.2f}s avg)"
    )
    
    return processed_results
