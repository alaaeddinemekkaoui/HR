"""
Redis caching utilities for HR application
"""
from django.core.cache import cache
from django.db.models import QuerySet
from typing import Optional, List, Any
import json


class CacheKeys:
    """Cache key constants"""
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


def get_cached_queryset(cache_key: str, queryset_func, ttl: int = CacheTTL.MEDIUM, 
                        select_related: Optional[List[str]] = None,
                        prefetch_related: Optional[List[str]] = None) -> QuerySet:
    """
    Get a cached queryset or execute the query and cache it
    
    Args:
        cache_key: Unique cache key
        queryset_func: Function that returns the queryset
        ttl: Time to live in seconds
        select_related: List of related fields to select
        prefetch_related: List of related fields to prefetch
    
    Returns:
        QuerySet result
    """
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return cached_data
    
    # Execute queryset
    queryset = queryset_func()
    
    # Apply optimizations
    if select_related:
        queryset = queryset.select_related(*select_related)
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    
    # Convert to list to cache the actual data
    result = list(queryset)
    
    # Cache the result
    cache.set(cache_key, result, ttl)
    
    return result


def get_cached_value(cache_key: str, value_func, ttl: int = CacheTTL.MEDIUM) -> Any:
    """
    Get a cached value or compute it and cache it
    
    Args:
        cache_key: Unique cache key
        value_func: Function that computes the value
        ttl: Time to live in seconds
    
    Returns:
        Cached or computed value
    """
    cached_value = cache.get(cache_key)
    
    if cached_value is not None:
        return cached_value
    
    value = value_func()
    cache.set(cache_key, value, ttl)
    
    return value


def invalidate_employee_cache(employee_id: Optional[int] = None):
    """Invalidate employee-related cache"""
    cache.delete(CacheKeys.EMPLOYEE_LIST)
    
    if employee_id:
        cache.delete(CacheKeys.EMPLOYEE_DETAIL.format(id=employee_id))


def invalidate_org_cache():
    """Invalidate organizational structure cache"""
    from django_redis import get_redis_connection
    try:
        conn = get_redis_connection("default")
        # Delete all keys matching org:*
        keys = conn.keys('hr_app:org:*')  # Include KEY_PREFIX
        if keys:
            conn.delete(*keys)
    except Exception:
        # Fallback: delete known keys individually
        cache.delete(CacheKeys.DIRECTIONS_ALL)
        cache.delete(CacheKeys.DIVISIONS_ALL)
        cache.delete(CacheKeys.SERVICES_ALL)
        cache.delete(CacheKeys.DEPARTEMENTS_ALL)
        cache.delete(CacheKeys.FILIERES_ALL)


def invalidate_taxonomy_cache():
    """Invalidate grades and positions cache"""
    cache.delete(CacheKeys.GRADES_ALL)
    cache.delete(CacheKeys.POSITIONS_ALL)


def invalidate_user_cache(user_id: int):
    """Invalidate user-specific cache"""
    cache.delete(CacheKeys.USER_GROUPS.format(id=user_id))
    cache.delete(CacheKeys.USER_PERMISSIONS.format(id=user_id))


def clear_all_cache():
    """Clear all application cache"""
    cache.clear()
