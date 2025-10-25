from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.roles.models import RoleDefinition, FunctionPermission, RolePermissionMapping


class Command(BaseCommand):
    help = "Seed function permissions and map them to roles"

    def handle(self, *args, **options):
        # Define available functions
        functions = [
            ('employees.view', 'View Employees', 'employees', 'View employee list and details'),
            ('employees.add', 'Add Employees', 'employees', 'Create new employees'),
            ('employees.edit', 'Edit Employees', 'employees', 'Modify existing employees'),
            ('employees.delete', 'Delete Employees', 'employees', 'Remove employees'),
            ('employees.export', 'Export Employees', 'employees', 'Export employee data'),
            
            ('users.view', 'View Users', 'users', 'View user accounts'),
            ('users.manage', 'Manage Users', 'users', 'Create, edit, and delete users'),
            ('users.assign_roles', 'Assign User Roles', 'users', 'Assign groups/roles to users'),
            
            ('roles.view', 'View Roles', 'roles', 'View role definitions'),
            ('roles.manage', 'Manage Roles', 'roles', 'Create, edit, and delete roles'),
            ('roles.assign_permissions', 'Assign Role Permissions', 'roles', 'Assign functions to roles'),
            
            ('dashboard.access', 'Access Dashboard', 'dashboard', 'View admin dashboard'),
            ('reports.view', 'View Reports', 'reports', 'Access reports'),
            ('reports.generate', 'Generate Reports', 'reports', 'Create and export reports'),
        ]

        self.stdout.write('Creating function permissions...')
        for code, name, module, desc in functions:
            func, created = FunctionPermission.objects.get_or_create(
                code=code,
                defaults={'name': name, 'module': module, 'description': desc}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {code}'))

        # Define role mappings
        role_perms = {
            'IT Admin': [
                'employees.view', 'employees.add', 'employees.edit', 'employees.delete', 'employees.export',
                'users.view', 'users.manage', 'users.assign_roles',
                'roles.view', 'roles.manage', 'roles.assign_permissions',
                'dashboard.access', 'reports.view', 'reports.generate',
            ],
            'HR Admin': [
                'employees.view', 'employees.add', 'employees.edit', 'employees.delete', 'employees.export',
                'roles.view',
                'dashboard.access', 'reports.view', 'reports.generate',
            ],
            'HR Edit': [
                'employees.view', 'employees.add', 'employees.edit', 'employees.export',
                'reports.view',
            ],
            'HR Add': [
                'employees.view', 'employees.add',
            ],
            'HR View': [
                'employees.view',
            ],
        }

        self.stdout.write('Mapping permissions to roles...')
        for role_name, perm_codes in role_perms.items():
            group, _ = Group.objects.get_or_create(name=role_name)
            role_def, created = RoleDefinition.objects.get_or_create(
                group=group,
                defaults={
                    'description': f'{role_name} role with predefined permissions',
                    'is_system_role': True
                }
            )
            
            # Clear existing mappings
            RolePermissionMapping.objects.filter(role=role_def).delete()
            
            # Add new mappings
            for code in perm_codes:
                try:
                    func = FunctionPermission.objects.get(code=code)
                    RolePermissionMapping.objects.create(role=role_def, function=func)
                except FunctionPermission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Function not found: {code}'))
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Mapped {len(perm_codes)} permissions to {role_name}'))

        self.stdout.write(self.style.SUCCESS('Function permissions seeded successfully!'))
