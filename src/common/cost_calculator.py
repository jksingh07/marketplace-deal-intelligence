"""
Cost Calculator for LLM Usage

Calculates costs based on token usage and model pricing.
Uses current OpenAI pricing as of 2024.
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Token usage for a single API call."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str


# OpenAI Pricing (per 1M tokens) - Updated as of 2024
# Source: https://openai.com/api/pricing/
OPENAI_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {
        "prompt": 2.50,      # $2.50 per 1M input tokens
        "completion": 10.00  # $10.00 per 1M output tokens
    },
    "gpt-4o-2024-08-06": {
        "prompt": 2.50,
        "completion": 10.00
    },
    "gpt-4o-mini": {
        "prompt": 0.15,      # $0.15 per 1M input tokens
        "completion": 0.60   # $0.60 per 1M output tokens
    },
    "gpt-4o-mini-2024-07-18": {
        "prompt": 0.15,
        "completion": 0.60
    },
    "gpt-4-turbo": {
        "prompt": 10.00,
        "completion": 30.00
    },
    "gpt-4-turbo-2024-04-09": {
        "prompt": 10.00,
        "completion": 30.00
    },
    "gpt-4": {
        "prompt": 30.00,
        "completion": 60.00
    },
    "gpt-3.5-turbo": {
        "prompt": 0.50,
        "completion": 1.50
    },
    "gpt-3.5-turbo-0125": {
        "prompt": 0.50,
        "completion": 1.50
    },
}


def get_model_pricing(model: str) -> Optional[Dict[str, float]]:
    """
    Get pricing for a model.
    
    Args:
        model: Model name (e.g., "gpt-4o-mini")
        
    Returns:
        Dict with "prompt" and "completion" prices per 1M tokens, or None if unknown
    """
    # Try exact match first
    if model in OPENAI_PRICING:
        return OPENAI_PRICING[model]
    
    # Try matching base model name (e.g., "gpt-4o-mini" matches "gpt-4o-mini-2024-07-18")
    for model_name, pricing in OPENAI_PRICING.items():
        if model_name.startswith(model) or model.startswith(model_name.split("-")[0]):
            return pricing
    
    return None


def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str
) -> Tuple[float, Optional[Dict[str, float]]]:
    """
    Calculate cost for a single API call.
    
    Args:
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        model: Model name used
        
    Returns:
        Tuple of (total_cost_usd, pricing_info_dict or None if model unknown)
    """
    pricing = get_model_pricing(model)
    
    if pricing is None:
        return 0.0, None
    
    # Calculate cost: (tokens / 1M) * price_per_1M
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
    total_cost = prompt_cost + completion_cost
    
    pricing_info = {
        "prompt_price_per_1M": pricing["prompt"],
        "completion_price_per_1M": pricing["completion"],
        "prompt_cost": prompt_cost,
        "completion_cost": completion_cost,
        "total_cost": total_cost,
    }
    
    return total_cost, pricing_info


def calculate_batch_cost(
    token_usages: list[TokenUsage]
) -> Dict[str, any]:
    """
    Calculate total cost for multiple API calls.
    
    Args:
        token_usages: List of TokenUsage objects
        
    Returns:
        Dict with total cost, breakdown by model, and statistics
    """
    total_cost = 0.0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    model_breakdown: Dict[str, Dict[str, any]] = {}
    unknown_models = set()
    
    for usage in token_usages:
        cost, pricing_info = calculate_cost(
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.model
        )
        
        total_cost += cost
        total_prompt_tokens += usage.prompt_tokens
        total_completion_tokens += usage.completion_tokens
        
        if pricing_info is None:
            unknown_models.add(usage.model)
        else:
            if usage.model not in model_breakdown:
                model_breakdown[usage.model] = {
                    "calls": 0,
                    "total_cost": 0.0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "pricing": pricing_info
                }
            
            model_breakdown[usage.model]["calls"] += 1
            model_breakdown[usage.model]["total_cost"] += cost
            model_breakdown[usage.model]["prompt_tokens"] += usage.prompt_tokens
            model_breakdown[usage.model]["completion_tokens"] += usage.completion_tokens
    
    return {
        "total_cost_usd": total_cost,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_prompt_tokens + total_completion_tokens,
        "model_breakdown": model_breakdown,
        "unknown_models": list(unknown_models),
    }


def format_cost(cost_usd: float) -> str:
    """
    Format cost in a human-readable way.
    
    Args:
        cost_usd: Cost in USD
        
    Returns:
        Formatted string (e.g., "$0.0012" or "$1.23")
    """
    if cost_usd < 0.01:
        return f"${cost_usd:.6f}"
    elif cost_usd < 1.0:
        return f"${cost_usd:.4f}"
    else:
        return f"${cost_usd:.2f}"
