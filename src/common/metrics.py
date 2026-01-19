"""
Metrics Collection Module

Provides simple metrics collection for monitoring pipeline performance.
In production, this would integrate with Prometheus, DataDog, etc.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict
from contextlib import contextmanager
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Collects and stores metrics for pipeline monitoring.
    
    Thread-safe implementation for use in concurrent environments.
    """
    
    def __init__(self):
        self._lock = Lock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
    
    def increment(self, name: str, value: float = 1.0, tags: Dict[str, str] = None) -> None:
        """
        Increment a counter metric.
        
        Args:
            name: Metric name
            value: Value to add (default 1)
            tags: Optional tags for grouping
        """
        key = self._make_key(name, tags)
        with self._lock:
            self._counters[key] += value
        logger.debug(f"Metric increment: {key}={value}")
    
    def gauge(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """
        Set a gauge metric (point-in-time value).
        
        Args:
            name: Metric name
            value: Current value
            tags: Optional tags for grouping
        """
        key = self._make_key(name, tags)
        with self._lock:
            self._gauges[key] = value
        logger.debug(f"Metric gauge: {key}={value}")
    
    def histogram(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """
        Record a histogram value (for distributions).
        
        Args:
            name: Metric name
            value: Value to record
            tags: Optional tags for grouping
        """
        key = self._make_key(name, tags)
        with self._lock:
            self._histograms[key].append(value)
        logger.debug(f"Metric histogram: {key}={value}")
    
    def timing(self, name: str, value_ms: float, tags: Dict[str, str] = None) -> None:
        """
        Record a timing metric (latency).
        
        Args:
            name: Metric name
            value_ms: Duration in milliseconds
            tags: Optional tags for grouping
        """
        key = self._make_key(name, tags)
        with self._lock:
            self._timers[key].append(value_ms)
        logger.debug(f"Metric timing: {key}={value_ms}ms")
    
    @contextmanager
    def timer(self, name: str, tags: Dict[str, str] = None):
        """
        Context manager for timing code blocks.
        
        Args:
            name: Metric name
            tags: Optional tags for grouping
            
        Example:
            with metrics.timer("llm_extraction"):
                result = call_llm()
        """
        start = time.time()
        try:
            yield
        finally:
            elapsed_ms = (time.time() - start) * 1000
            self.timing(name, elapsed_ms, tags)
    
    def get_counter(self, name: str, tags: Dict[str, str] = None) -> float:
        """Get current counter value."""
        key = self._make_key(name, tags)
        with self._lock:
            return self._counters.get(key, 0.0)
    
    def get_gauge(self, name: str, tags: Dict[str, str] = None) -> Optional[float]:
        """Get current gauge value."""
        key = self._make_key(name, tags)
        with self._lock:
            return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """
        Get histogram statistics.
        
        Returns:
            Dict with count, min, max, avg, p50, p95, p99
        """
        key = self._make_key(name, tags)
        with self._lock:
            values = self._histograms.get(key, [])
        
        if not values:
            return {"count": 0}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "avg": sum(sorted_values) / count,
            "p50": self._percentile(sorted_values, 50),
            "p95": self._percentile(sorted_values, 95),
            "p99": self._percentile(sorted_values, 99),
        }
    
    def get_timer_stats(self, name: str, tags: Dict[str, str] = None) -> Dict[str, float]:
        """Get timer statistics (same format as histogram)."""
        key = self._make_key(name, tags)
        with self._lock:
            values = self._timers.get(key, [])
        
        if not values:
            return {"count": 0}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "min_ms": sorted_values[0],
            "max_ms": sorted_values[-1],
            "avg_ms": sum(sorted_values) / count,
            "p50_ms": self._percentile(sorted_values, 50),
            "p95_ms": self._percentile(sorted_values, 95),
            "p99_ms": self._percentile(sorted_values, 99),
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {k: self.get_histogram_stats(k) for k in self._histograms},
                "timers": {k: self.get_timer_stats(k) for k in self._timers},
            }
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()
    
    def _make_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Create a metric key from name and tags."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"
    
    @staticmethod
    def _percentile(sorted_values: List[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        k = (len(sorted_values) - 1) * percentile / 100
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_values) else f
        return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])


# Global metrics collector instance
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


# Convenience functions
def increment(name: str, value: float = 1.0, tags: Dict[str, str] = None) -> None:
    """Increment a counter metric."""
    get_metrics().increment(name, value, tags)


def gauge(name: str, value: float, tags: Dict[str, str] = None) -> None:
    """Set a gauge metric."""
    get_metrics().gauge(name, value, tags)


def histogram(name: str, value: float, tags: Dict[str, str] = None) -> None:
    """Record a histogram value."""
    get_metrics().histogram(name, value, tags)


def timing(name: str, value_ms: float, tags: Dict[str, str] = None) -> None:
    """Record a timing metric."""
    get_metrics().timing(name, value_ms, tags)


def timer(name: str, tags: Dict[str, str] = None):
    """Context manager for timing code blocks."""
    return get_metrics().timer(name, tags)


# ============================================================================
# Stage 4 Specific Metrics
# ============================================================================

def record_extraction_metrics(
    listing_id: str,
    llm_used: bool,
    llm_latency_ms: Optional[float] = None,
    tokens_used: Optional[int] = None,
    signals_extracted: int = 0,
    validation_passed: bool = True,
) -> None:
    """
    Record metrics for a single extraction.
    
    Args:
        listing_id: Listing identifier
        llm_used: Whether LLM was used
        llm_latency_ms: LLM call latency in ms
        tokens_used: Total tokens used
        signals_extracted: Number of signals extracted
        validation_passed: Whether schema validation passed
    """
    metrics = get_metrics()
    
    # Count extractions
    metrics.increment("stage4.extractions_total")
    
    if llm_used:
        metrics.increment("stage4.extractions_with_llm")
        if llm_latency_ms:
            metrics.timing("stage4.llm_latency", llm_latency_ms)
        if tokens_used:
            metrics.histogram("stage4.tokens_used", tokens_used)
    else:
        metrics.increment("stage4.extractions_guardrails_only")
    
    # Signal counts
    metrics.histogram("stage4.signals_per_extraction", signals_extracted)
    
    # Validation
    if validation_passed:
        metrics.increment("stage4.validation_passed")
    else:
        metrics.increment("stage4.validation_failed")


def record_signal_metrics(
    category: str,
    signal_type: str,
    severity: str,
    verification_level: str,
) -> None:
    """
    Record metrics for a detected signal.
    
    Args:
        category: Signal category
        signal_type: Signal type
        severity: Signal severity
        verification_level: Verification level
    """
    metrics = get_metrics()
    
    # Count by category
    metrics.increment("stage4.signals_by_category", tags={"category": category})
    
    # Count by severity
    metrics.increment("stage4.signals_by_severity", tags={"severity": severity})
    
    # Count by verification level
    metrics.increment(
        "stage4.signals_by_verification",
        tags={"verification": verification_level}
    )
