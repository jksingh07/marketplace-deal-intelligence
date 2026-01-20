"""
Cost Tracking for LLM Usage

Tracks token usage by model for cost calculation.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from threading import Lock

from common.cost_calculator import TokenUsage, calculate_batch_cost, format_cost


@dataclass
class ModelTokenUsage:
    """Token usage aggregated by model."""
    model: str
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class CostTracker:
    """
    Thread-safe tracker for token usage by model.
    
    Stores individual token usage records for accurate cost calculation.
    """
    
    def __init__(self):
        self._lock = Lock()
        self._usage_records: List[TokenUsage] = []
    
    def record_usage(self, token_usage: TokenUsage) -> None:
        """Record token usage for a single API call."""
        with self._lock:
            self._usage_records.append(token_usage)
    
    def get_all_usage(self) -> List[TokenUsage]:
        """Get all recorded token usage."""
        with self._lock:
            return list(self._usage_records)
    
    def get_model_breakdown(self) -> Dict[str, ModelTokenUsage]:
        """Get token usage aggregated by model."""
        with self._lock:
            breakdown: Dict[str, ModelTokenUsage] = {}
            
            for usage in self._usage_records:
                if usage.model not in breakdown:
                    breakdown[usage.model] = ModelTokenUsage(model=usage.model)
                
                model_stats = breakdown[usage.model]
                model_stats.calls += 1
                model_stats.prompt_tokens += usage.prompt_tokens
                model_stats.completion_tokens += usage.completion_tokens
                model_stats.total_tokens += usage.total_tokens
            
            return breakdown
    
    def get_cost_summary(self) -> Dict:
        """Get cost summary with breakdown by model."""
        usage_list = self.get_all_usage()
        if not usage_list:
            return {
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "model_breakdown": {},
                "unknown_models": [],
            }
        
        return calculate_batch_cost(usage_list)
    
    def reset(self) -> None:
        """Reset all tracked usage."""
        with self._lock:
            self._usage_records.clear()


# Global cost tracker instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker


def record_token_usage(token_usage: TokenUsage) -> None:
    """Record token usage for cost tracking."""
    get_cost_tracker().record_usage(token_usage)
