from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction

from apps.employees.models import (
    Employee, EmploymentHistory, Service, Division, Direction, Position, Grade, GradeProgressionRule
)
from apps.leaves.models import (
    LeaveRequest, EmployeeLeaveBalance, LeaveType
)
from apps.roles.models import RoleDefinition, RolePermissionMapping


class Command(BaseCommand):
    help = "Reset HR domain data (employees, org, leaves). Keeps auth users and roles currently assigned to at least one user. Removes unused roles."

    def add_arguments(self, parser):
        parser.add_argument('--noinput', action='store_true', help='Run without confirmation prompt')

    def handle(self, *args, **options):
        noinput = options.get('noinput')
        if not noinput:
            confirm = input('This will DELETE employees, org (directions/divisions/services), grades, positions, leaves, and unused roles. Continue? [y/N]: ')
            if confirm.strip().lower() != 'y':
                self.stdout.write(self.style.WARNING('Aborted.'))
                return

        with transaction.atomic():
            # 1) Remove leaves first (requests, balances), then types
            self.stdout.write('Deleting leave requests and balances...')
            LeaveRequest.objects.all().delete()
            EmployeeLeaveBalance.objects.all().delete()
            self.stdout.write('Deleting leave types...')
            LeaveType.objects.all().delete()

            # 2) Remove employees and their histories
            self.stdout.write('Deleting employees and employment history...')
            EmploymentHistory.objects.all().delete()
            Employee.objects.all().delete()

            # 3) Remove org units and catalogs (services -> divisions -> directions; positions, grades, rules)
            self.stdout.write('Deleting org units and catalogs...')
            Service.objects.all().delete()
            Division.objects.all().delete()
            Direction.objects.all().delete()
            GradeProgressionRule.objects.all().delete()
            Position.objects.all().delete()
            Grade.objects.all().delete()

            # 4) Prune roles not assigned to any user (keep only roles in use)
            self.stdout.write('Pruning unused roles...')
            roles = RoleDefinition.objects.select_related('group').all()
            for role in roles:
                group = role.group
                if group.user_set.exists():
                    continue  # keep roles in use
                # delete mappings, role, and backing group
                RolePermissionMapping.objects.filter(role=role).delete()
                role.delete()
                try:
                    group.delete()
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS('✅ Domain data reset completed. Users and roles in use were preserved.'))
