"""
Caching Module

Provides caching for expensive operations like LLM calls and guardrail processing.
"""

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable
from threading import Lock
from collections import OrderedDict

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A single cache entry."""
    value: Any
    created_at: float
    expires_at: float
    hits: int = 0


@dataclass
class CacheConfig:
    """Configuration for the cache."""
    max_size: int = 1000
    default_ttl_seconds: float = 3600.0  # 1 hour
    enable_stats: bool = True


class LRUCache:
    """
    Thread-safe LRU cache with TTL support.
    
    Features:
    - LRU eviction when max size reached
    - TTL-based expiration
    - Thread-safe operations
    - Stats tracking
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        
        # Stats
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if time.time() > entry.expires_at:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._hits += 1
            
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl or self.config.default_ttl_seconds
        now = time.time()
        
        with self._lock:
            # Remove if exists
            if key in self._cache:
                del self._cache[key]
            
            # Evict oldest if at capacity
            while len(self._cache) >= self.config.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._evictions += 1
            
            # Add new entry
            self._cache[key] = CacheEntry(
                value=value,
                created_at=now,
                expires_at=now + ttl,
            )
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_size": self.config.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_rate": hit_rate,
            }


def make_cache_key(*args, **kwargs) -> str:
    """
    Create a cache key from arguments.
    
    Uses MD5 hash for consistent, fixed-length keys.
    """
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def make_text_hash(text: str) -> str:
    """Create a hash from text content."""
    return hashlib.md5(text.encode()).hexdigest()


# ============================================================================
# Global Caches
# ============================================================================

# Cache for guardrail results
_guardrails_cache: Optional[LRUCache] = None

# Cache for LLM results
_llm_cache: Optional[LRUCache] = None


def get_guardrails_cache() -> LRUCache:
    """Get the guardrails result cache."""
    global _guardrails_cache
    if _guardrails_cache is None:
        _guardrails_cache = LRUCache(CacheConfig(
            max_size=1000,
            default_ttl_seconds=86400.0,  # 24 hours (guardrails are deterministic)
        ))
    return _guardrails_cache


def get_llm_cache() -> LRUCache:
    """Get the LLM result cache."""
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = LRUCache(CacheConfig(
            max_size=500,
            default_ttl_seconds=3600.0,  # 1 hour (LLM results may change)
        ))
    return _llm_cache


def cached_guardrails(func: Callable) -> Callable:
    """
    Decorator to cache guardrail results.
    
    Example:
        @cached_guardrails
        def run_guardrails(prepared_text):
            ...
    """
    def wrapper(*args, **kwargs):
        # Create cache key from text content
        if args and hasattr(args[0], 'combined_text'):
            text_hash = make_text_hash(args[0].combined_text)
        else:
            text_hash = make_cache_key(*args, **kwargs)
        
        cache = get_guardrails_cache()
        
        # Check cache
        result = cache.get(text_hash)
        if result is not None:
            logger.debug(f"Guardrails cache hit: {text_hash[:8]}")
            return result
        
        # Execute and cache
        logger.debug(f"Guardrails cache miss: {text_hash[:8]}")
        result = func(*args, **kwargs)
        cache.set(text_hash, result)
        
        return result
    
    return wrapper


def cached_llm_extraction(func: Callable) -> Callable:
    """
    Decorator to cache LLM extraction results.
    
    Example:
        @cached_llm_extraction
        def extract_with_llm(listing_id, title, description, ...):
            ...
    """
    def wrapper(*args, **kwargs):
        # Create cache key from title and description
        title = kwargs.get('title', args[2] if len(args) > 2 else '')
        description = kwargs.get('description', args[3] if len(args) > 3 else '')
        
        text_hash = make_text_hash(f"{title}\n{description}")
        cache = get_llm_cache()
        
        # Check cache
        result = cache.get(text_hash)
        if result is not None:
            logger.debug(f"LLM cache hit: {text_hash[:8]}")
            return result
        
        # Execute and cache
        logger.debug(f"LLM cache miss: {text_hash[:8]}")
        result = func(*args, **kwargs)
        
        # Only cache successful results
        if result and result.get("payload"):
            cache.set(text_hash, result)
        
        return result
    
    return wrapper


def get_all_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches."""
    return {
        "guardrails": get_guardrails_cache().get_stats(),
        "llm": get_llm_cache().get_stats(),
    }


def clear_all_caches() -> None:
    """Clear all caches."""
    get_guardrails_cache().clear()
    get_llm_cache().clear()
    logger.info("All caches cleared")
