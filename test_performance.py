#!/usr/bin/env python
"""
Performance Testing Script for Redis Cache Optimization
Tests query speed with and without caching
"""
import os
import sys
import django
import time
from statistics import mean, median

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.core.cache import cache
from apps.employees.models import Employee, Direction, Division, Service
from apps.employees.cache import get_cached_queryset, CacheKeys, CacheTTL


def clear_cache():
    """Clear all cache"""
    cache.clear()
    print("✓ Cache cleared")


def measure_query_time(func, iterations=10):
    """Measure average query time"""
    times = []
    for i in range(iterations):
        start = time.time()
        result = func()
        end = time.time()
        times.append((end - start) * 1000)  # Convert to milliseconds
    return {
        'avg': mean(times),
        'median': median(times),
        'min': min(times),
        'max': max(times),
        'times': times
    }


def test_employee_list_without_cache():
    """Query employees without cache"""
    return list(Employee.objects.select_related(
        'direction', 'division', 'service', 'departement', 
        'filiere', 'grade', 'position', 'user'
    ).prefetch_related('user__groups').all())


def test_employee_list_with_cache():
    """Query employees with cache"""
    return get_cached_queryset(
        CacheKeys.EMPLOYEE_LIST,
        lambda: Employee.objects.all(),
        ttl=CacheTTL.MEDIUM,
        select_related=['direction', 'division', 'service', 'departement', 
                       'filiere', 'grade', 'position', 'user'],
        prefetch_related=['user__groups']
    )


def test_directions_without_cache():
    """Query directions without cache"""
    return list(Direction.objects.filter(is_active=True).order_by('name'))


def test_divisions_by_direction_without_cache(direction_id=1):
    """Query divisions by direction without cache"""
    return list(Division.objects.filter(
        direction_id=direction_id, is_active=True
    ).values('id', 'name'))


def test_divisions_by_direction_with_cache(direction_id=1):
    """Query divisions by direction with cache"""
    cache_key = CacheKeys.DIVISIONS_BY_DIRECTION.format(id=direction_id)
    divisions = cache.get(cache_key)
    if divisions is None:
        divisions = list(Division.objects.filter(
            direction_id=direction_id, is_active=True
        ).values('id', 'name'))
        cache.set(cache_key, divisions, CacheTTL.LONG)
    return divisions


def run_performance_tests():
    """Run all performance tests"""
    print("=" * 80)
    print("PERFORMANCE TESTING - Redis Cache Optimization")
    print("=" * 80)
    print()
    
    # Get baseline data
    employee_count = Employee.objects.count()
    direction_count = Direction.objects.count()
    division_count = Division.objects.count()
    
    print(f"📊 Database Stats:")
    print(f"   Employees: {employee_count}")
    print(f"   Directions: {direction_count}")
    print(f"   Divisions: {division_count}")
    print()
    
    # Test 1: Employee List Query
    print("🔍 Test 1: Employee List Query (with related data)")
    print("-" * 80)
    
    # Without cache (first run)
    clear_cache()
    print("Without cache (cold start):")
    no_cache_results = measure_query_time(test_employee_list_without_cache, iterations=5)
    print(f"   Average: {no_cache_results['avg']:.2f} ms")
    print(f"   Median:  {no_cache_results['median']:.2f} ms")
    print(f"   Min:     {no_cache_results['min']:.2f} ms")
    print(f"   Max:     {no_cache_results['max']:.2f} ms")
    print()
    
    # With cache (first run - cache miss)
    clear_cache()
    print("With cache (first run - cache miss):")
    first_cache_result = measure_query_time(test_employee_list_with_cache, iterations=1)
    print(f"   Time: {first_cache_result['avg']:.2f} ms")
    print()
    
    # With cache (subsequent runs - cache hit)
    print("With cache (cache hit - 10 runs):")
    cache_results = measure_query_time(test_employee_list_with_cache, iterations=10)
    print(f"   Average: {cache_results['avg']:.2f} ms")
    print(f"   Median:  {cache_results['median']:.2f} ms")
    print(f"   Min:     {cache_results['min']:.2f} ms")
    print(f"   Max:     {cache_results['max']:.2f} ms")
    print()
    
    speedup = no_cache_results['avg'] / cache_results['avg']
    print(f"⚡ Speedup: {speedup:.2f}x faster with cache!")
    print(f"   Time saved: {no_cache_results['avg'] - cache_results['avg']:.2f} ms per request")
    print()
    
    # Test 2: Cascading Dropdown (Divisions by Direction)
    print("🔍 Test 2: Cascading Dropdown - Divisions by Direction")
    print("-" * 80)
    
    # Check if we have directions
    if direction_count > 0:
        # Without cache
        clear_cache()
        print("Without cache:")
        no_cache_div_results = measure_query_time(
            lambda: test_divisions_by_direction_without_cache(direction_id=1), 
            iterations=10
        )
        print(f"   Average: {no_cache_div_results['avg']:.2f} ms")
        print(f"   Median:  {no_cache_div_results['median']:.2f} ms")
        print()
        
        # With cache (first run)
        clear_cache()
        first_div_cache = measure_query_time(
            lambda: test_divisions_by_direction_with_cache(direction_id=1), 
            iterations=1
        )
        print(f"With cache (first run): {first_div_cache['avg']:.2f} ms")
        
        # With cache (subsequent runs)
        cache_div_results = measure_query_time(
            lambda: test_divisions_by_direction_with_cache(direction_id=1), 
            iterations=10
        )
        print(f"With cache (cache hit):")
        print(f"   Average: {cache_div_results['avg']:.2f} ms")
        print(f"   Median:  {cache_div_results['median']:.2f} ms")
        print()
        
        div_speedup = no_cache_div_results['avg'] / cache_div_results['avg']
        print(f"⚡ Speedup: {div_speedup:.2f}x faster with cache!")
        print()
    
    # Test 3: Cache Statistics
    print("📈 Redis Cache Statistics")
    print("-" * 80)
    
    # Check cache keys
    try:
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        
        # Get all cache keys
        keys = redis_conn.keys('hr_app:*')
        print(f"   Total cached keys: {len(keys)}")
        
        # Show some cache keys
        if keys:
            print(f"   Sample keys:")
            for key in list(keys)[:5]:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                ttl = redis_conn.ttl(key)
                print(f"      - {key_str} (TTL: {ttl}s)")
        
        # Get Redis info
        info = redis_conn.info('stats')
        print(f"\n   Redis Stats:")
        print(f"      Total connections: {info.get('total_connections_received', 'N/A')}")
        print(f"      Total commands: {info.get('total_commands_processed', 'N/A')}")
        print(f"      Keyspace hits: {info.get('keyspace_hits', 'N/A')}")
        print(f"      Keyspace misses: {info.get('keyspace_misses', 'N/A')}")
        
        if info.get('keyspace_hits') and info.get('keyspace_misses'):
            hit_rate = (info['keyspace_hits'] / 
                       (info['keyspace_hits'] + info['keyspace_misses'])) * 100
            print(f"      Hit rate: {hit_rate:.2f}%")
        
    except Exception as e:
        print(f"   ⚠ Could not get Redis stats: {e}")
    
    print()
    
    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Employee List Query:")
    print(f"   Without cache: {no_cache_results['avg']:.2f} ms")
    print(f"   With cache:    {cache_results['avg']:.2f} ms")
    print(f"   Improvement:   {speedup:.2f}x faster ({((speedup-1)*100):.1f}% reduction)")
    print()
    
    if direction_count > 0:
        print(f"Cascading Dropdown Query:")
        print(f"   Without cache: {no_cache_div_results['avg']:.2f} ms")
        print(f"   With cache:    {cache_div_results['avg']:.2f} ms")
        print(f"   Improvement:   {div_speedup:.2f}x faster ({((div_speedup-1)*100):.1f}% reduction)")
        print()
    
    print("✅ Performance testing completed!")
    print()
    print("💡 Tips:")
    print("   - First request will be slower (cache miss)")
    print("   - Subsequent requests use cached data (much faster)")
    print("   - Cache automatically invalidates when data changes")
    print("   - Monitor with: docker compose exec redis redis-cli MONITOR")
    print()


if __name__ == '__main__':
    run_performance_tests()
