"""
Core app - Base classes and utilities
"""
from .cache import (
    get_cache,
    cache_key,
    cached,
    cache_get_or_set,
    cache_delete_pattern,
    invalidate_model_cache,
    CacheMixin,
)

__all__ = [
    'get_cache',
    'cache_key',
    'cached',
    'cache_get_or_set',
    'cache_delete_pattern',
    'invalidate_model_cache',
    'CacheMixin',
]
