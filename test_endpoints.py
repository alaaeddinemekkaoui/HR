#!/usr/bin/env python
"""
Quick health check for HR System endpoints
Run inside container: docker compose exec web python test_endpoints.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse

# Create test request
factory = RequestFactory()

# Test URL resolution
endpoints = [
    # Employees
    ('employees:list', 'Employee List'),
    ('employees:create', 'Create Employee'),
    ('employees:org_directions', 'Directions'),
    ('employees:org_divisions', 'Divisions'),
    ('employees:org_services', 'Services'),
    ('employees:rules_list', 'Grade Rules'),
    
    # Authentication
    ('authentication:profile', 'Profile'),
    ('authentication:users', 'Users List'),
    
    # Roles
    ('roles:groups', 'Groups'),
    ('roles:roles', 'Roles'),
    
    # Leaves
    ('leaves:types', 'Leave Types'),
    ('leaves:my', 'My Leaves'),
    ('leaves:request', 'Request Leave'),
    ('leaves:approve', 'Leave Approvals'),
]

print("🔍 HR System Endpoint Health Check\n")
print("=" * 60)

success = 0
failed = 0

for url_name, description in endpoints:
    try:
        url = reverse(url_name)
        print(f"✅ {description:30} → {url}")
        success += 1
    except Exception as e:
        print(f"❌ {description:30} → ERROR: {e}")
        failed += 1

print("=" * 60)
print(f"\n📊 Results: {success} passed, {failed} failed\n")

if failed == 0:
    print("🎉 All endpoints are properly configured!")
else:
    print(f"⚠️  {failed} endpoint(s) need attention")
