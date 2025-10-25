from typing import List
from django.contrib.auth.models import User
from django.db.models import Q
from apps.employees.models.employee import Employee, Position


def find_supervisors_for(employee: Employee) -> List[User]:
    """Return a list of Users who should act as supervisors for the given employee.
    Preference order: Chef de Service in same service, then Chef de Division in same division,
    then Chef de Direction in same direction. Only returns those with linked user accounts.
    """
    users: List[User] = []

    # Try service-level supervisor
    if employee.service_id:
        qs = Employee.objects.filter(
            service_id=employee.service_id,
            position__position_type='chef_service',
        ).select_related('user')
        users.extend([e.user for e in qs if e.user])
        if users:
            return users

    # Try division-level supervisor
    if employee.division_id:
        qs = Employee.objects.filter(
            division_id=employee.division_id,
            position__position_type='chef_division',
        ).select_related('user')
        users.extend([e.user for e in qs if e.user])
        if users:
            return users

    # Fallback to direction-level supervisor
    qs = Employee.objects.filter(
        direction_id=employee.direction_id,
        position__position_type='chef_direction',
    ).select_related('user')
    users.extend([e.user for e in qs if e.user])
    return users


def approvals_scope_q_for_user(user: User) -> Q:
    """Return a Q filter limiting LeaveRequest.employee to the scope managed by this user.
    Superuser or HR Admin can see all; otherwise:
      - chef_service: same service
      - chef_division: same division
      - chef_direction: same direction
    Non-supervisors: see none.
    """
    # Superusers or HR Admin see all
    if user.is_superuser or user.groups.filter(name__in=['HR Admin', 'IT Admin']).exists():
        return Q()  # no restriction

    emp = getattr(user, 'employee_profile', None)
    if not emp or not emp.position_id:
        return Q(pk__in=[])  # nothing

    ptype = getattr(emp.position, 'position_type', None)
    # Direct-assignment scopes only:
    # - chef_service: employees directly assigned to the same service
    # - chef_division: employees assigned to the division (no service)
    # - chef_direction: employees assigned directly to direction (no division/service)
    if ptype == 'chef_service' and emp.service_id:
        return Q(employee__service_id=emp.service_id)
    if ptype == 'chef_division' and emp.division_id:
        return Q(employee__division_id=emp.division_id, employee__service__isnull=True)
    if ptype == 'chef_direction' and emp.direction_id:
        return Q(employee__direction_id=emp.direction_id, employee__division__isnull=True, employee__service__isnull=True)

    return Q(pk__in=[])
