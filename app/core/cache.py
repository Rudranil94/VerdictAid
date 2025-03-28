from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache as fastapi_cache
from redis import asyncio as aioredis
from typing import Optional, Any, Callable
from app.core.config import settings
import pickle
import hashlib
import json

class CustomCache:
    def __init__(self):
        self.redis = None
    
    async def init_cache(self):
        """Initialize Redis cache connection."""
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf8",
            decode_responses=True
        )
        FastAPICache.init(
            RedisBackend(self.redis),
            prefix="verdict_aid_cache:"
        )
    
    def cache(
        self,
        expire: int = 60,
        namespace: Optional[str] = None,
        key_builder: Optional[Callable] = None
    ):
        """
        Custom cache decorator with enhanced functionality.
        
        Args:
            expire: Cache expiration time in seconds
            namespace: Optional namespace for the cache key
            key_builder: Optional function to build custom cache keys
        """
        def default_key_builder(
            func,
            namespace: Optional[str] = None,
            *args,
            **kwargs,
        ):
            """Build default cache key based on function arguments."""
            prefix = namespace or func.__name__
            # Convert args and kwargs to a stable string representation
            cache_dict = {
                "args": args,
                "kwargs": kwargs
            }
            cache_str = json.dumps(cache_dict, sort_keys=True)
            # Create hash of the arguments
            key = hashlib.sha256(cache_str.encode()).hexdigest()
            return f"{prefix}:{key}"
        
        return fastapi_cache(
            expire=expire,
            namespace=namespace,
            key_builder=key_builder or default_key_builder
        )
    
    async def get_or_set(
        self,
        key: str,
        value_func: Callable,
        expire: int = 60,
        namespace: Optional[str] = None
    ) -> Any:
        """
        Get value from cache or compute and store it.
        
        Args:
            key: Cache key
            value_func: Function to compute value if not in cache
            expire: Cache expiration time in seconds
            namespace: Optional namespace for the cache key
        """
        if namespace:
            key = f"{namespace}:{key}"
        
        # Try to get from cache
        cached_value = await self.redis.get(key)
        if cached_value is not None:
            return pickle.loads(cached_value)
        
        # Compute value
        value = await value_func()
        
        # Store in cache
        await self.redis.set(
            key,
            pickle.dumps(value),
            ex=expire
        )
        
        return value
    
    async def invalidate(
        self,
        key: str,
        namespace: Optional[str] = None
    ):
        """
        Invalidate a cached value.
        
        Args:
            key: Cache key to invalidate
            namespace: Optional namespace for the cache key
        """
        if namespace:
            key = f"{namespace}:{key}"
        await self.redis.delete(key)
    
    async def invalidate_pattern(
        self,
        pattern: str,
        namespace: Optional[str] = None
    ):
        """
        Invalidate all cached values matching a pattern.
        
        Args:
            pattern: Pattern to match cache keys
            namespace: Optional namespace for the cache key
        """
        if namespace:
            pattern = f"{namespace}:{pattern}"
        
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
    
    async def clear_all(self):
        """Clear all cached values."""
        await self.redis.flushdb()

# Create global cache instance
cache_service = CustomCache()
