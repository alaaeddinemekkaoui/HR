from typing import Iterable, Optional
from django.db.models import QuerySet
from django.core.cache import cache
from ..models import Employee
from ..cache import get_cached_queryset, CacheKeys, CacheTTL


def list_employees() -> QuerySet[Employee]:
    """Get all employees with optimized caching and select_related.

    Returns a list (materialized queryset) — callers in views expect an iterable and
    apply additional filters on it. We provide a callable to the cache helper.
    """
    return get_cached_queryset(
        CacheKeys.EMPLOYEE_LIST,
        lambda: Employee.objects.all(),
        ttl=CacheTTL.MEDIUM,
        select_related=['direction', 'division', 'service', 'departement', 'filiere', 'grade', 'position'],
        prefetch_related=['user__groups']
    )


def get_employee(pk: int) -> Optional[Employee]:
    """Get a single employee with caching.

    We cache the materialized instance. If not present, fetch from DB and cache it.
    """
    cache_key = CacheKeys.EMPLOYEE_DETAIL.format(id=pk)

    employee = cache.get(cache_key)
    if employee is not None:
        return employee

    try:
        employee = Employee.objects.select_related(
            'direction', 'division', 'service', 'departement', 'filiere', 'grade', 'position', 'user'
        ).prefetch_related('user__groups').get(pk=pk)
        cache.set(cache_key, employee, CacheTTL.MEDIUM)
        return employee
    except Employee.DoesNotExist:
        return None


def create_employee(**data) -> Employee:
    return Employee.objects.create(**data)


def update_employee(employee: Employee, **data) -> Employee:
    for k, v in data.items():
        setattr(employee, k, v)
    employee.save()
    return employee


def delete_employee(employee: Employee) -> None:
    employee.delete()
