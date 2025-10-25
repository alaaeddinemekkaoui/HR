from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from apps.employees.models import Employee, Direction, Division, Service, Grade, Position


class Command(BaseCommand):
    help = "Seed default RBAC groups and permissions for the employees app"

    def handle(self, *args, **options):
        # Ensure groups exist
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        hr_group, _ = Group.objects.get_or_create(name="HR")
        employee_group, _ = Group.objects.get_or_create(name="Employee")

        # Collect content types
        models = [Employee, Direction, Division, Service, Grade, Position]
        content_types = {m.__name__: ContentType.objects.get_for_model(m) for m in models}

        # Helper to fetch permissions for a model
        def perms_for(model_cls, codenames):
            ct = content_types[model_cls.__name__]
            return list(Permission.objects.filter(content_type=ct, codename__in=codenames))

        # Admin: all permissions in employees app
        all_employees_app_perms = Permission.objects.filter(content_type__in=content_types.values())
        admin_group.permissions.set(all_employees_app_perms)

        # HR: manage employees (add/change/view), view reference data
        hr_perms = []
        hr_perms += perms_for(Employee, ["view_employee", "add_employee", "change_employee"])  # no delete by default
        for ref_model in [Direction, Division, Service, Grade, Position]:
            hr_perms += perms_for(ref_model, [f"view_{ref_model.__name__.lower()}"])
        hr_group.permissions.set(hr_perms)

        # Employee: can view employees (read-only)
        employee_view_perms = perms_for(Employee, ["view_employee"]) 
        employee_group.permissions.set(employee_view_perms)

        self.stdout.write(self.style.SUCCESS("RBAC groups and permissions seeded: Admin, HR, Employee"))
