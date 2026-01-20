"""
Persistent Cost Tracker

Stores token usage and costs to a file so they persist across sessions.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from threading import Lock

from common.cost_calculator import TokenUsage, calculate_cost

logger = logging.getLogger(__name__)


@dataclass
class UsageRecord:
    """Single usage record with timestamp."""
    timestamp: str
    listing_id: Optional[str]
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class PersistentCostTracker:
    """
    Tracks token usage and costs persistently across sessions.
    
    Stores data in a JSON file that accumulates over time.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize persistent tracker.
        
        Args:
            storage_path: Path to JSON file for storage (defaults to project root)
        """
        if storage_path is None:
            # Default to project root / .metrics/usage_history.json
            project_root = Path(__file__).parent.parent.parent
            metrics_dir = project_root / ".metrics"
            metrics_dir.mkdir(exist_ok=True)
            storage_path = metrics_dir / "usage_history.json"
        
        self.storage_path = storage_path
        self._lock = Lock()
        self._records: List[UsageRecord] = []
        self._load()
    
    def _load(self) -> None:
        """Load existing records from file."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self._records = [
                    UsageRecord(**record) for record in data.get("records", [])
                ]
            logger.debug(f"Loaded {len(self._records)} usage records from {self.storage_path}")
        except Exception as e:
            logger.warning(f"Failed to load usage history: {e}")
            self._records = []
    
    def _save(self) -> None:
        """Save records to file."""
        try:
            with self._lock:
                data = {
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "total_records": len(self._records),
                    "records": [asdict(record) for record in self._records]
                }
                
                # Write atomically (write to temp file, then rename)
                temp_path = self.storage_path.with_suffix('.tmp')
                with open(temp_path, 'w') as f:
                    json.dump(data, f, indent=2)
                temp_path.replace(self.storage_path)
                
                logger.debug(f"Saved {len(self._records)} usage records to {self.storage_path}")
                
                # Auto-generate summary report
                try:
                    from common.usage_report_generator import generate_usage_report
                    generate_usage_report()
                except Exception as e:
                    logger.debug(f"Failed to auto-generate usage report: {e}")
        except Exception as e:
            logger.error(f"Failed to save usage history: {e}")
    
    def record_usage(
        self,
        token_usage: TokenUsage,
        listing_id: Optional[str] = None
    ) -> None:
        """
        Record token usage and calculate cost.
        
        Args:
            token_usage: TokenUsage object from API call
            listing_id: Optional listing ID for reference
        """
        cost, _ = calculate_cost(
            token_usage.prompt_tokens,
            token_usage.completion_tokens,
            token_usage.model
        )
        
        record = UsageRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            listing_id=listing_id,
            model=token_usage.model,
            prompt_tokens=token_usage.prompt_tokens,
            completion_tokens=token_usage.completion_tokens,
            total_tokens=token_usage.total_tokens,
            cost_usd=cost
        )
        
        with self._lock:
            self._records.append(record)
        
        self._save()
    
    def get_cumulative_stats(self) -> Dict:
        """
        Get cumulative statistics across all sessions.
        
        Returns:
            Dict with total tokens, costs, breakdown by model, etc.
        """
        with self._lock:
            if not self._records:
                return {
                    "total_calls": 0,
                    "total_tokens": 0,
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0,
                    "total_cost_usd": 0.0,
                    "model_breakdown": {},
                    "first_record": None,
                    "last_record": None,
                }
            
            total_tokens = sum(r.total_tokens for r in self._records)
            total_prompt = sum(r.prompt_tokens for r in self._records)
            total_completion = sum(r.completion_tokens for r in self._records)
            total_cost = sum(r.cost_usd for r in self._records)
            
            # Breakdown by model
            model_breakdown: Dict[str, Dict] = {}
            for record in self._records:
                if record.model not in model_breakdown:
                    model_breakdown[record.model] = {
                        "calls": 0,
                        "total_tokens": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_cost": 0.0,
                    }
                
                model_breakdown[record.model]["calls"] += 1
                model_breakdown[record.model]["total_tokens"] += record.total_tokens
                model_breakdown[record.model]["prompt_tokens"] += record.prompt_tokens
                model_breakdown[record.model]["completion_tokens"] += record.completion_tokens
                model_breakdown[record.model]["total_cost"] += record.cost_usd
            
            return {
                "total_calls": len(self._records),
                "total_tokens": total_tokens,
                "total_prompt_tokens": total_prompt,
                "total_completion_tokens": total_completion,
                "total_cost_usd": total_cost,
                "model_breakdown": model_breakdown,
                "first_record": self._records[0].timestamp if self._records else None,
                "last_record": self._records[-1].timestamp if self._records else None,
            }
    
    def get_recent_usage(self, limit: int = 10) -> List[UsageRecord]:
        """Get most recent usage records."""
        with self._lock:
            return self._records[-limit:] if limit > 0 else list(self._records)
    
    def reset(self) -> None:
        """Reset all records (clears file)."""
        with self._lock:
            self._records.clear()
        self._save()
        logger.info("Usage history reset")


# Global persistent tracker instance
_persistent_tracker: Optional[PersistentCostTracker] = None


def get_persistent_tracker() -> PersistentCostTracker:
    """Get the global persistent cost tracker."""
    global _persistent_tracker
    if _persistent_tracker is None:
        _persistent_tracker = PersistentCostTracker()
    return _persistent_tracker


def record_usage_persistent(
    token_usage: TokenUsage,
    listing_id: Optional[str] = None
) -> None:
    """Record token usage persistently."""
    get_persistent_tracker().record_usage(token_usage, listing_id)
