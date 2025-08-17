"""
Advanced caching system for API responses and database queries.
Provides Redis-based caching with fallback to in-memory caching.
"""

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union

import structlog

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = structlog.get_logger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration settings."""

    redis_url: Optional[str] = None
    default_ttl: int = 300  # 5 minutes
    max_memory_cache_size: int = 1000
    enable_compression: bool = True
    key_prefix: str = "sentigen:"


class CacheManager:
    """Advanced cache manager with Redis and in-memory fallback."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0, "errors": 0}

    async def initialize(self):
        """Initialize cache connections."""
        if REDIS_AVAILABLE and self.config.redis_url:
            try:
                self.redis_client = redis.from_url(
                    self.config.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning("Redis connection failed, using memory cache", error=str(e))
                self.redis_client = None
        else:
            logger.info("Using in-memory cache (Redis not available)")

    def _generate_key(self, key: str) -> str:
        """Generate cache key with prefix."""
        return f"{self.config.key_prefix}{key}"

    def _serialize_value(self, value: Any) -> str:
        """Serialize value for caching."""
        try:
            return json.dumps(value, default=str, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to serialize cache value", error=str(e))
            return json.dumps({"error": "serialization_failed"})

    def _deserialize_value(self, value: str) -> Any:
        """Deserialize cached value."""
        try:
            return json.loads(value)
        except Exception as e:
            logger.error("Failed to deserialize cache value", error=str(e))
            return None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        cache_key = self._generate_key(key)

        try:
            # Try Redis first
            if self.redis_client:
                try:
                    value = await self.redis_client.get(cache_key)
                    if value:
                        self.cache_stats["hits"] += 1
                        return self._deserialize_value(value)
                except Exception as e:
                    logger.error("Redis get failed", key=cache_key, error=str(e))
                    self.cache_stats["errors"] += 1

            # Fallback to memory cache
            if cache_key in self.memory_cache:
                cache_entry = self.memory_cache[cache_key]
                if cache_entry["expires_at"] > datetime.utcnow():
                    self.cache_stats["hits"] += 1
                    return cache_entry["value"]
                else:
                    # Expired, remove from memory cache
                    del self.memory_cache[cache_key]

            self.cache_stats["misses"] += 1
            return None

        except Exception as e:
            logger.error("Cache get failed", key=cache_key, error=str(e))
            self.cache_stats["errors"] += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        cache_key = self._generate_key(key)
        ttl = ttl or self.config.default_ttl
        serialized_value = self._serialize_value(value)

        try:
            # Try Redis first
            if self.redis_client:
                try:
                    await self.redis_client.setex(cache_key, ttl, serialized_value)
                    self.cache_stats["sets"] += 1
                    return True
                except Exception as e:
                    logger.error("Redis set failed", key=cache_key, error=str(e))
                    self.cache_stats["errors"] += 1

            # Fallback to memory cache
            # Clean up expired entries if cache is getting large
            if len(self.memory_cache) >= self.config.max_memory_cache_size:
                await self._cleanup_memory_cache()

            self.memory_cache[cache_key] = {"value": value, "expires_at": datetime.utcnow() + timedelta(seconds=ttl)}
            self.cache_stats["sets"] += 1
            return True

        except Exception as e:
            logger.error("Cache set failed", key=cache_key, error=str(e))
            self.cache_stats["errors"] += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        cache_key = self._generate_key(key)

        try:
            # Delete from Redis
            if self.redis_client:
                try:
                    await self.redis_client.delete(cache_key)
                except Exception as e:
                    logger.error("Redis delete failed", key=cache_key, error=str(e))

            # Delete from memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]

            return True

        except Exception as e:
            logger.error("Cache delete failed", key=cache_key, error=str(e))
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        deleted_count = 0

        try:
            # Clear from Redis
            if self.redis_client:
                try:
                    keys = await self.redis_client.keys(f"{self.config.key_prefix}{pattern}")
                    if keys:
                        deleted_count += await self.redis_client.delete(*keys)
                except Exception as e:
                    logger.error("Redis pattern clear failed", pattern=pattern, error=str(e))

            # Clear from memory cache
            keys_to_delete = [
                key
                for key in self.memory_cache.keys()
                if key.startswith(f"{self.config.key_prefix}{pattern.replace('*', '')}")
            ]
            for key in keys_to_delete:
                del self.memory_cache[key]
                deleted_count += 1

            return deleted_count

        except Exception as e:
            logger.error("Cache pattern clear failed", pattern=pattern, error=str(e))
            return 0

    async def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache."""
        now = datetime.utcnow()
        expired_keys = [key for key, entry in self.memory_cache.items() if entry["expires_at"] <= now]
        for key in expired_keys:
            del self.memory_cache[key]

        logger.debug("Memory cache cleanup", expired_count=len(expired_keys))

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "memory_cache_size": len(self.memory_cache),
            "redis_connected": self.redis_client is not None,
        }


def cache_response(key_func: Optional[Callable] = None, ttl: int = 300, skip_cache_if: Optional[Callable] = None):
    """
    Decorator for caching API responses.

    Args:
        key_func: Function to generate cache key from function args
        ttl: Time to live in seconds
        skip_cache_if: Function to determine if caching should be skipped
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager from app state or create default
            cache_manager = getattr(wrapper, "_cache_manager", None)
            if not cache_manager:
                return await func(*args, **kwargs)

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # Check if caching should be skipped
            if skip_cache_if and skip_cache_if(*args, **kwargs):
                return await func(*args, **kwargs)

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# Global cache manager instance
cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> Optional[CacheManager]:
    """Get the global cache manager instance."""
    return cache_manager


def initialize_cache(config: CacheConfig) -> CacheManager:
    """Initialize the global cache manager."""
    global cache_manager
    cache_manager = CacheManager(config)
    return cache_manager
