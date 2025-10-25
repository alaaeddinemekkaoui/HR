from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from apps.employees.models import Employee


class Command(BaseCommand):
    help = "Seed RBAC groups: IT Admin (all), HR View, HR Add, HR Edit (no delete)"

    def handle(self, *args, **options):
        # Ensure groups exist
        it_admin, _ = Group.objects.get_or_create(name="IT Admin")
        

        # Employee model permissions
        employee_ct = ContentType.objects.get_for_model(Employee)
        def get_perms(codes):
            return list(Permission.objects.filter(content_type=employee_ct, codename__in=codes))

        view_perm = get_perms(["view_employee"])   # list/detail
        add_perm = get_perms(["add_employee"])     # create
        change_perm = get_perms(["change_employee"]) # edit
        delete_perm = get_perms(["delete_employee"]) # delete

        # Assign perms
        it_admin.permissions.set(view_perm + add_perm + change_perm + delete_perm)


        self.stdout.write(self.style.SUCCESS("Seeded groups: IT Admin, HR View, HR Add, HR Edit"))
