"""
Circuit Breaker Module

Implements the circuit breaker pattern to prevent cascading failures
when external services (like OpenAI) are experiencing issues.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Generic
from threading import Lock
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5          # Failures to trip the circuit
    success_threshold: int = 3          # Successes to close the circuit
    timeout_seconds: float = 60.0       # Time before attempting recovery
    half_open_max_calls: int = 1        # Calls allowed in half-open state
    

class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open and call is rejected."""
    
    def __init__(self, breaker_name: str, time_until_retry: float):
        self.breaker_name = breaker_name
        self.time_until_retry = time_until_retry
        super().__init__(
            f"Circuit breaker '{breaker_name}' is open. "
            f"Retry in {time_until_retry:.1f}s"
        )


class CircuitBreaker:
    """
    Circuit breaker for external service calls.
    
    States:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Service failing, calls are rejected immediately
    - HALF_OPEN: Testing recovery, limited calls allowed
    
    Example:
        breaker = CircuitBreaker("openai")
        
        try:
            with breaker.call():
                result = call_openai()
        except CircuitBreakerOpen:
            # Use fallback
            result = fallback_result()
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            self._check_state_transition()
            return self._state
    
    def _check_state_transition(self) -> None:
        """Check if state should transition (called within lock)."""
        if self._state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self._last_failure_time:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.timeout_seconds:
                    logger.info(
                        f"Circuit breaker '{self.name}' transitioning to HALF_OPEN "
                        f"after {elapsed:.1f}s"
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0
    
    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.debug(
                    f"Circuit breaker '{self.name}' half-open success "
                    f"({self._success_count}/{self.config.success_threshold})"
                )
                
                if self._success_count >= self.config.success_threshold:
                    logger.info(f"Circuit breaker '{self.name}' closed (service recovered)")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = max(0, self._failure_count - 1)
    
    def record_failure(self, error: Optional[Exception] = None) -> None:
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                logger.warning(
                    f"Circuit breaker '{self.name}' opening (failed in half-open state)"
                )
                self._state = CircuitState.OPEN
                
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    logger.warning(
                        f"Circuit breaker '{self.name}' opening "
                        f"(threshold reached: {self._failure_count})"
                    )
                    self._state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        """Check if a call can be executed."""
        with self._lock:
            self._check_state_transition()
            
            if self._state == CircuitState.CLOSED:
                return True
                
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
            
            # OPEN state
            return False
    
    def time_until_retry(self) -> float:
        """Get time in seconds until retry is allowed."""
        with self._lock:
            if self._state != CircuitState.OPEN:
                return 0.0
            
            if self._last_failure_time is None:
                return 0.0
            
            elapsed = time.time() - self._last_failure_time
            remaining = self.config.timeout_seconds - elapsed
            return max(0.0, remaining)
    
    def call(self):
        """
        Context manager for circuit-breaker protected calls.
        
        Raises:
            CircuitBreakerOpen: If circuit is open
        """
        return CircuitBreakerContext(self)
    
    async def call_async(self):
        """
        Async context manager for circuit-breaker protected calls.
        
        Raises:
            CircuitBreakerOpen: If circuit is open
        """
        return CircuitBreakerContextAsync(self)
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "time_until_retry": self.time_until_retry(),
            }
    
    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            logger.info(f"Circuit breaker '{self.name}' reset to CLOSED")


class CircuitBreakerContext:
    """Context manager for synchronous circuit breaker usage."""
    
    def __init__(self, breaker: CircuitBreaker):
        self.breaker = breaker
    
    def __enter__(self):
        if not self.breaker.can_execute():
            raise CircuitBreakerOpen(
                self.breaker.name,
                self.breaker.time_until_retry()
            )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.breaker.record_success()
        else:
            self.breaker.record_failure(exc_val)
        return False  # Don't suppress exceptions


class CircuitBreakerContextAsync:
    """Async context manager for circuit breaker usage."""
    
    def __init__(self, breaker: CircuitBreaker):
        self.breaker = breaker
    
    async def __aenter__(self):
        if not self.breaker.can_execute():
            raise CircuitBreakerOpen(
                self.breaker.name,
                self.breaker.time_until_retry()
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.breaker.record_success()
        else:
            self.breaker.record_failure(exc_val)
        return False


# ============================================================================
# Global Circuit Breakers
# ============================================================================

_openai_breaker: Optional[CircuitBreaker] = None


def get_openai_circuit_breaker() -> CircuitBreaker:
    """Get the OpenAI API circuit breaker."""
    global _openai_breaker
    if _openai_breaker is None:
        _openai_breaker = CircuitBreaker(
            "openai",
            CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout_seconds=60.0,
            )
        )
    return _openai_breaker


def circuit_breaker_protected(breaker: CircuitBreaker):
    """
    Decorator to protect a function with a circuit breaker.
    
    Example:
        @circuit_breaker_protected(get_openai_circuit_breaker())
        def call_openai():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with breaker.call():
                return func(*args, **kwargs)
        return wrapper
    return decorator


def circuit_breaker_protected_async(breaker: CircuitBreaker):
    """
    Decorator to protect an async function with a circuit breaker.
    
    Example:
        @circuit_breaker_protected_async(get_openai_circuit_breaker())
        async def call_openai():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with breaker.call_async():
                return await func(*args, **kwargs)
        return wrapper
    return decorator
