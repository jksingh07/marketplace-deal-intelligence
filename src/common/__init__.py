"""
Common utilities and models for the AI Pipeline.

Includes:
- Models: Pydantic models for type safety
- Schema Enums: Centralized enum definitions from JSON schema
- Logging: Structured logging configuration
- Metrics: Metrics collection for monitoring
- Rate Limiter: API rate limiting
- Circuit Breaker: Failure handling
- Caching: Result caching
- Input Validation: Input sanitization
"""

from common.models import (
    Signal,
    MaintenanceClaim,
    MaintenanceRedFlag,
    FollowUpQuestion,
    VerificationLevel,
    Severity,
    ClaimedCondition,
    ServiceHistoryLevel,
    ModsRiskLevel,
    NegotiationStance,
    RiskLevelOverall,
)

from common.schema_enums import (
    get_all_signal_types,
    is_valid_signal_type,
    is_valid_evidence_present,
)

from common.logging_config import (
    setup_logging,
    get_logger,
)

from common.metrics import (
    get_metrics,
    increment,
    gauge,
    histogram,
    timing,
    timer,
)

from common.rate_limiter import (
    RateLimiter,
    get_openai_rate_limiter,
    configure_openai_rate_limit,
    rate_limited,
)

from common.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
    get_openai_circuit_breaker,
    circuit_breaker_protected,
)

from common.caching import (
    LRUCache,
    get_guardrails_cache,
    get_llm_cache,
    get_all_cache_stats,
    clear_all_caches,
)

from common.input_validation import (
    InputValidator,
    ValidationResult,
    validate_listing,
    validate_and_sanitize,
)

__all__ = [
    # Models
    "Signal",
    "MaintenanceClaim",
    "MaintenanceRedFlag",
    "FollowUpQuestion",
    "VerificationLevel",
    "Severity",
    "ClaimedCondition",
    "ServiceHistoryLevel",
    "ModsRiskLevel",
    "NegotiationStance",
    "RiskLevelOverall",
    # Schema enums
    "get_all_signal_types",
    "is_valid_signal_type",
    "is_valid_evidence_present",
    # Logging
    "setup_logging",
    "get_logger",
    # Metrics
    "get_metrics",
    "increment",
    "gauge",
    "histogram",
    "timing",
    "timer",
    # Rate limiting
    "RateLimiter",
    "get_openai_rate_limiter",
    "configure_openai_rate_limit",
    "rate_limited",
    # Circuit breaker
    "CircuitBreaker",
    "CircuitBreakerOpen",
    "get_openai_circuit_breaker",
    "circuit_breaker_protected",
    # Caching
    "LRUCache",
    "get_guardrails_cache",
    "get_llm_cache",
    "get_all_cache_stats",
    "clear_all_caches",
    # Input validation
    "InputValidator",
    "ValidationResult",
    "validate_listing",
    "validate_and_sanitize",
]
