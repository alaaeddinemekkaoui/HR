from typing import Iterable, Optional
from django.db.models import QuerySet
from ..models import Employee


def list_employees() -> QuerySet[Employee]:
    return Employee.objects.all()


def get_employee(pk: int) -> Optional[Employee]:
    try:
        return Employee.objects.get(pk=pk)
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
