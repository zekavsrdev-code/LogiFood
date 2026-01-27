"""
Redis Cache Utilities for LogiFood
"""
from functools import wraps
from typing import Any, Callable, Optional
from django.core.cache import cache
from django.core.cache.backends.base import BaseCache


def get_cache() -> BaseCache:
    """Get the default cache instance"""
    return cache


def cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments
    
    Usage:
        key = cache_key('user', user_id=123, role='supplier')
        # Returns: 'logifood:user:user_id=123:role=supplier'
    """
    parts = []
    for arg in args:
        if arg:
            parts.append(str(arg))
    
    for key, value in sorted(kwargs.items()):
        if value is not None:
            parts.append(f"{key}={value}")
    
    return ':'.join(parts)


def cached(timeout: int = 300, key_func: Optional[Callable] = None, version: Optional[int] = None):
    """
    Decorator to cache function results
    
    Args:
        timeout: Cache timeout in seconds (default: 300 = 5 minutes)
        key_func: Optional function to generate cache key from function arguments
        version: Optional cache version
    
    Usage:
        @cached(timeout=600)
        def get_categories():
            return Category.objects.all()
        
        @cached(timeout=300, key_func=lambda user_id: f'user:{user_id}')
        def get_user_profile(user_id):
            return User.objects.get(id=user_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                # Default: use function name + args + kwargs
                key_parts = [func.__module__, func.__name__]
                if args:
                    key_parts.extend(str(arg) for arg in args)
                if kwargs:
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key_str = ':'.join(key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key_str, version=version)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key_str, result, timeout, version=version)
            return result
        
        # Add cache invalidation method
        def invalidate(*args, **kwargs):
            """Invalidate cache for this function"""
            if key_func:
                cache_key_str = key_func(*args, **kwargs)
            else:
                key_parts = [func.__module__, func.__name__]
                if args:
                    key_parts.extend(str(arg) for arg in args)
                if kwargs:
                    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key_str = ':'.join(key_parts)
            cache.delete(cache_key_str, version=version)
        
        wrapper.invalidate = invalidate
        return wrapper
    return decorator


def cache_get_or_set(key: str, callable_func: Callable, timeout: int = 300, version: Optional[int] = None) -> Any:
    """
    Get value from cache or set it using callable
    
    Args:
        key: Cache key
        callable_func: Function to call if cache miss
        timeout: Cache timeout in seconds
        version: Optional cache version
    
    Returns:
        Cached or computed value
    
    Usage:
        categories = cache_get_or_set(
            'categories:all',
            lambda: list(Category.objects.filter(is_active=True)),
            timeout=600
        )
    """
    value = cache.get(key, version=version)
    if value is None:
        value = callable_func()
        cache.set(key, value, timeout, version=version)
    return value


def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all cache keys matching a pattern
    
    Args:
        pattern: Pattern to match (supports wildcards like 'categories:*')
    
    Returns:
        Number of keys deleted
    
    Note: This uses Redis SCAN which may be slow on large datasets.
    Only works with Redis cache backend. Returns 0 if backend is not Redis.
    """
    # Check if cache backend is Redis
    if not hasattr(cache, 'client') or not hasattr(cache.client, 'get_client'):
        # Not a Redis backend (e.g., dummy cache in tests)
        return 0
    
    try:
        # Get Redis client from Django cache client
        redis_client = cache.client.get_client(write=True)
        deleted_count = 0
        
        # Convert Django cache key prefix to Redis pattern
        cache_prefix = cache.make_key('')
        full_pattern = f"{cache_prefix}{pattern}"
        
        # Use SCAN to find matching keys
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match=full_pattern, count=100)
            if keys:
                redis_client.delete(*keys)
                deleted_count += len(keys)
            if cursor == 0:
                break
        
        return deleted_count
    except (AttributeError, NotImplementedError, Exception):
        # Redis not available or backend doesn't support this feature
        # Silently return 0 (test environment or Redis not configured)
        return 0


def invalidate_model_cache(model_class, instance_id: Optional[int] = None):
    """
    Invalidate cache for a model
    
    Args:
        model_class: Django model class
        instance_id: Optional specific instance ID, if None invalidates all
    
    Usage:
        invalidate_model_cache(Category)
        invalidate_model_cache(Product, product_id=123)
    """
    model_name = model_class.__name__.lower()
    
    if instance_id:
        # Invalidate specific instance
        patterns = [
            f"{model_name}:{instance_id}:*",
            f"{model_name}:list:*",
            f"{model_name}:all",
        ]
    else:
        # Invalidate all instances
        patterns = [
            f"{model_name}:*",
        ]
    
    for pattern in patterns:
        cache_delete_pattern(pattern)


class CacheMixin:
    """Mixin to add cache utilities to classes"""
    
    @staticmethod
    def get_cache_key(*args, **kwargs) -> str:
        """Generate cache key"""
        return cache_key(*args, **kwargs)
    
    @staticmethod
    def get_from_cache(key: str, default: Any = None) -> Any:
        """Get value from cache"""
        return cache.get(key, default)
    
    @staticmethod
    def set_to_cache(key: str, value: Any, timeout: int = 300) -> bool:
        """Set value to cache"""
        return cache.set(key, value, timeout)
    
    @staticmethod
    def delete_from_cache(key: str) -> bool:
        """Delete value from cache"""
        return cache.delete(key)
    
    @staticmethod
    def clear_cache_pattern(pattern: str) -> int:
        """Clear cache by pattern"""
        return cache_delete_pattern(pattern)
