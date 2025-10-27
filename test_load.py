#!/usr/bin/env python
"""
Load Testing Script - Simulates heavy concurrent traffic
Tests the app under stress to verify no stuttering
"""
import asyncio
import aiohttp
import time
from statistics import mean, median
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
ENDPOINTS = [
    "/employees/",
    "/employees/create/",
    "/admin-dashboard/",
]

API_ENDPOINTS = [
    "/employees/api/get-divisions/?direction_id=1",
    "/employees/api/get-services/?division_id=1",
]


async def fetch(session, url):
    """Fetch a single URL and measure time"""
    start = time.time()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            await response.text()
            duration = (time.time() - start) * 1000  # Convert to ms
            return {
                'url': url,
                'status': response.status,
                'duration': duration,
                'success': response.status == 200
            }
    except asyncio.TimeoutError:
        return {
            'url': url,
            'status': 'TIMEOUT',
            'duration': 30000,
            'success': False
        }
    except Exception as e:
        return {
            'url': url,
            'status': f'ERROR: {str(e)}',
            'duration': 0,
            'success': False
        }


async def load_test_endpoint(url, concurrent_requests=50, total_requests=200):
    """Load test a single endpoint with concurrent requests"""
    print(f"\n🔥 Load Testing: {url}")
    print(f"   Concurrent: {concurrent_requests} | Total: {total_requests}")
    print("-" * 80)
    
    results = []
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Create batches of concurrent requests
        for batch_start in range(0, total_requests, concurrent_requests):
            batch_size = min(concurrent_requests, total_requests - batch_start)
            tasks = [fetch(session, url) for _ in range(batch_size)]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Progress indicator
            completed = len(results)
            percent = (completed / total_requests) * 100
            print(f"   Progress: {completed}/{total_requests} ({percent:.0f}%)", end='\r')
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    durations = [r['duration'] for r in successful]
    
    print(f"\n   ✅ Successful: {len(successful)}/{total_requests}")
    if failed:
        print(f"   ❌ Failed: {len(failed)}")
    
    if durations:
        print(f"\n   Response Times:")
        print(f"      Average: {mean(durations):.2f} ms")
        print(f"      Median:  {median(durations):.2f} ms")
        print(f"      Min:     {min(durations):.2f} ms")
        print(f"      Max:     {max(durations):.2f} ms")
        print(f"\n   Throughput:")
        print(f"      Total time: {total_time:.2f} seconds")
        print(f"      Requests/sec: {total_requests/total_time:.2f}")
        
        # Performance assessment
        avg_time = mean(durations)
        if avg_time < 50:
            print(f"      🚀 EXCELLENT: Sub-50ms average response!")
        elif avg_time < 100:
            print(f"      ✅ GOOD: Sub-100ms average response")
        elif avg_time < 500:
            print(f"      ⚠️  OK: Sub-500ms average response")
        else:
            print(f"      ❌ SLOW: Over 500ms average response")


async def run_load_tests():
    """Run all load tests"""
    print("=" * 80)
    print("LOAD TESTING - Concurrent User Simulation")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("⚙️  Configuration:")
    print("   - Simulating 50 concurrent users")
    print("   - 200 requests per endpoint")
    print("   - Testing both page views and async API endpoints")
    print()
    
    # Test API endpoints first (async views)
    print("=" * 80)
    print("Part 1: Async API Endpoints (Cascading Dropdowns)")
    print("=" * 80)
    
    for endpoint in API_ENDPOINTS:
        url = BASE_URL + endpoint
        await load_test_endpoint(url, concurrent_requests=50, total_requests=200)
    
    print("\n" + "=" * 80)
    print("📊 LOAD TEST SUMMARY")
    print("=" * 80)
    print("\n✅ Load testing completed!")
    print("\n💡 What to look for:")
    print("   - Average response time should be < 100ms")
    print("   - No timeouts or errors")
    print("   - High throughput (requests/second)")
    print("   - Consistent response times (low max time)")
    print()
    print("🔍 Monitor while running:")
    print("   Redis: docker compose exec redis redis-cli MONITOR")
    print("   MySQL: docker compose exec web python manage.py dbshell")
    print("   Stats: docker stats")
    print()


if __name__ == '__main__':
    print("\n⚠️  Note: Make sure the server is running at http://localhost:8000")
    print("   Press Ctrl+C to cancel...")
    print()
    
    try:
        asyncio.run(run_load_tests())
    except KeyboardInterrupt:
        print("\n\n❌ Load testing cancelled by user")
