"""
Rate Limiter Module

Provides rate limiting for API calls to prevent exceeding quotas.
"""

import asyncio
import logging
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    calls_per_minute: int = 60
    calls_per_second: int = 10
    burst_limit: int = 20  # Max calls in burst
    retry_on_limit: bool = True
    max_wait_seconds: float = 60.0


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Supports both synchronous and asynchronous usage.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self._lock = Lock()
        self._async_lock = asyncio.Lock() if asyncio else None
        
        # Token bucket state
        self._tokens = float(self.config.burst_limit)
        self._last_update = time.time()
        
        # Rate: tokens per second
        self._rate = self.config.calls_per_minute / 60.0
        
        # Call history for monitoring
        self._call_times: deque = deque(maxlen=1000)
    
    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_update
        self._tokens = min(
            self.config.burst_limit,
            self._tokens + elapsed * self._rate
        )
        self._last_update = now
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token (blocking).
        
        Args:
            timeout: Maximum time to wait for a token
            
        Returns:
            True if token acquired, False if timeout
        """
        timeout = timeout or self.config.max_wait_seconds
        deadline = time.time() + timeout
        
        while True:
            with self._lock:
                self._refill_tokens()
                
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    self._call_times.append(time.time())
                    return True
            
            # Check timeout
            remaining = deadline - time.time()
            if remaining <= 0:
                logger.warning("Rate limit acquire timeout")
                return False
            
            # Wait before retry
            wait_time = min(0.1, remaining)
            time.sleep(wait_time)
    
    async def acquire_async(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token (async).
        
        Args:
            timeout: Maximum time to wait for a token
            
        Returns:
            True if token acquired, False if timeout
        """
        timeout = timeout or self.config.max_wait_seconds
        deadline = time.time() + timeout
        
        while True:
            async with self._async_lock:
                self._refill_tokens()
                
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    self._call_times.append(time.time())
                    return True
            
            # Check timeout
            remaining = deadline - time.time()
            if remaining <= 0:
                logger.warning("Rate limit acquire timeout (async)")
                return False
            
            # Wait before retry
            wait_time = min(0.1, remaining)
            await asyncio.sleep(wait_time)
    
    @contextmanager
    def limit(self):
        """
        Context manager for rate-limited operations.
        
        Example:
            with rate_limiter.limit():
                call_api()
        """
        if not self.acquire():
            raise RateLimitExceeded("Rate limit exceeded")
        yield
    
    async def limit_async(self):
        """
        Async context manager for rate-limited operations.
        
        Example:
            async with rate_limiter.limit_async():
                await call_api()
        """
        if not await self.acquire_async():
            raise RateLimitExceeded("Rate limit exceeded (async)")
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        with self._lock:
            now = time.time()
            
            # Count calls in last minute
            calls_last_minute = sum(
                1 for t in self._call_times
                if now - t < 60
            )
            
            # Count calls in last second
            calls_last_second = sum(
                1 for t in self._call_times
                if now - t < 1
            )
            
            return {
                "tokens_available": self._tokens,
                "calls_last_minute": calls_last_minute,
                "calls_last_second": calls_last_second,
                "rate_per_minute": self.config.calls_per_minute,
            }


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded and retry is disabled."""
    pass


# Global rate limiters for different services
_openai_limiter: Optional[RateLimiter] = None


def get_openai_rate_limiter() -> RateLimiter:
    """Get the global OpenAI rate limiter."""
    global _openai_limiter
    if _openai_limiter is None:
        # Default: 60 calls/minute, burst of 10
        _openai_limiter = RateLimiter(RateLimitConfig(
            calls_per_minute=60,
            calls_per_second=3,
            burst_limit=10,
        ))
    return _openai_limiter


def configure_openai_rate_limit(
    calls_per_minute: int = 60,
    burst_limit: int = 10,
) -> None:
    """
    Configure the OpenAI rate limiter.
    
    Call this before making API calls to set custom limits.
    
    Args:
        calls_per_minute: Maximum calls per minute
        burst_limit: Maximum burst size
    """
    global _openai_limiter
    _openai_limiter = RateLimiter(RateLimitConfig(
        calls_per_minute=calls_per_minute,
        burst_limit=burst_limit,
    ))
    logger.info(
        f"OpenAI rate limit configured: {calls_per_minute}/min, burst={burst_limit}"
    )


def rate_limited(func: Callable) -> Callable:
    """
    Decorator for rate-limited functions.
    
    Example:
        @rate_limited
        def call_openai():
            ...
    """
    def wrapper(*args, **kwargs) -> Any:
        limiter = get_openai_rate_limiter()
        with limiter.limit():
            return func(*args, **kwargs)
    return wrapper


def rate_limited_async(func: Callable) -> Callable:
    """
    Decorator for rate-limited async functions.
    
    Example:
        @rate_limited_async
        async def call_openai():
            ...
    """
    async def wrapper(*args, **kwargs) -> Any:
        limiter = get_openai_rate_limiter()
        await limiter.limit_async()
        return await func(*args, **kwargs)
    return wrapper
