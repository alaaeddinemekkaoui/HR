"""
Async Redis caching utilities for high-performance operations under load
"""
from django.core.cache import cache
from django.db.models import QuerySet
from asgiref.sync import sync_to_async
from typing import Optional, List, Any, Callable
import asyncio


class CacheKeys:
    """Cache key constants - shared with sync cache.py"""
    # Employee caching
    EMPLOYEE_LIST = 'employees:list:all'
    EMPLOYEE_DETAIL = 'employees:detail:{id}'
    EMPLOYEE_BY_DIRECTION = 'employees:direction:{id}'
    
    # Organizational structure
    DIRECTIONS_ALL = 'org:directions:all'
    DIVISIONS_ALL = 'org:divisions:all'
    DIVISIONS_BY_DIRECTION = 'org:divisions:direction:{id}'
    SERVICES_ALL = 'org:services:all'
    SERVICES_BY_DIRECTION = 'org:services:direction:{id}'
    SERVICES_BY_DIVISION = 'org:services:division:{id}'
    DEPARTEMENTS_ALL = 'org:departements:all'
    FILIERES_ALL = 'org:filieres:all'
    FILIERES_BY_DEPARTEMENT = 'org:filieres:departement:{id}'
    
    # Grades and Positions
    GRADES_ALL = 'taxonomy:grades:all'
    POSITIONS_ALL = 'taxonomy:positions:all'
    
    # User permissions
    USER_GROUPS = 'user:groups:{id}'
    USER_PERMISSIONS = 'user:permissions:{id}'


class CacheTTL:
    """Cache time-to-live constants (in seconds)"""
    SHORT = 60 * 5  # 5 minutes
    MEDIUM = 60 * 15  # 15 minutes
    LONG = 60 * 60  # 1 hour
    VERY_LONG = 60 * 60 * 24  # 24 hours


# Convert sync cache operations to async
aget_cache = sync_to_async(cache.get, thread_sensitive=True)
aset_cache = sync_to_async(cache.set, thread_sensitive=True)
adelete_cache = sync_to_async(cache.delete, thread_sensitive=True)

# For delete_pattern, we need to use django_redis directly
@sync_to_async
def adelete_pattern(pattern: str):
    """Async delete by pattern using django-redis"""
    from django_redis import get_redis_connection
    try:
        conn = get_redis_connection("default")
        keys = conn.keys(pattern)
        if keys:
            conn.delete(*keys)
    except Exception:
        # Fallback: just pass if redis client unavailable
        pass


async def get_cached_queryset_async(
    cache_key: str,
    queryset_func: Callable,
    ttl: int = CacheTTL.MEDIUM,
    select_related: Optional[List[str]] = None,
    prefetch_related: Optional[List[str]] = None
) -> List[Any]:
    """
    Async version of get_cached_queryset for non-blocking cache operations
    
    Args:
        cache_key: Unique cache key
        queryset_func: Async function that returns the queryset
        ttl: Time to live in seconds
        select_related: List of related fields to select
        prefetch_related: List of related fields to prefetch
    
    Returns:
        List of model instances
    """
    # Try to get from cache first (non-blocking)
    cached_data = await aget_cache(cache_key)
    
    if cached_data is not None:
        return cached_data
    
    # Execute queryset (convert sync ORM to async)
    @sync_to_async
    def execute_query():
        queryset = queryset_func()
        
        # Apply optimizations
        if select_related:
            queryset = queryset.select_related(*select_related)
        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)
        
        # Materialize the queryset
        return list(queryset)
    
    result = await execute_query()
    
    # Cache the result (non-blocking)
    await aset_cache(cache_key, result, ttl)
    
    return result


async def get_cached_value_async(
    cache_key: str,
    value_func: Callable,
    ttl: int = CacheTTL.MEDIUM
) -> Any:
    """
    Async version of get_cached_value for non-blocking cache operations
    
    Args:
        cache_key: Unique cache key
        value_func: Async or sync function that computes the value
        ttl: Time to live in seconds
    
    Returns:
        Cached or computed value
    """
    cached_value = await aget_cache(cache_key)
    
    if cached_value is not None:
        return cached_value
    
    # Execute value function
    if asyncio.iscoroutinefunction(value_func):
        value = await value_func()
    else:
        value = await sync_to_async(value_func)()
    
    await aset_cache(cache_key, value, ttl)
    
    return value


async def invalidate_employee_cache_async(employee_id: Optional[int] = None):
    """Async invalidate employee-related cache"""
    await adelete_cache(CacheKeys.EMPLOYEE_LIST)
    
    if employee_id:
        await adelete_cache(CacheKeys.EMPLOYEE_DETAIL.format(id=employee_id))


async def invalidate_org_cache_async():
    """Async invalidate organizational structure cache"""
    await adelete_pattern('org:*')


async def invalidate_taxonomy_cache_async():
    """Async invalidate grades and positions cache"""
    await adelete_cache(CacheKeys.GRADES_ALL)
    await adelete_cache(CacheKeys.POSITIONS_ALL)


async def invalidate_user_cache_async(user_id: int):
    """Async invalidate user-specific cache"""
    await adelete_cache(CacheKeys.USER_GROUPS.format(id=user_id))
    await adelete_cache(CacheKeys.USER_PERMISSIONS.format(id=user_id))


async def clear_all_cache_async():
    """Async clear all application cache"""
    await sync_to_async(cache.clear)()


# Batch cache operations for efficiency
async def get_many_async(keys: List[str]) -> dict:
    """Get multiple cache keys in one operation"""
    return await sync_to_async(cache.get_many)(keys)


async def set_many_async(data: dict, ttl: int = CacheTTL.MEDIUM):
    """Set multiple cache keys in one operation"""
    await sync_to_async(cache.set_many)(data, ttl)


async def delete_many_async(keys: List[str]):
    """Delete multiple cache keys in one operation"""
    await sync_to_async(cache.delete_many)(keys)
