from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from apps.employees.models import Employee, Direction, Division, Service, Grade, Position
from apps.roles.models import RoleDefinition, FunctionPermission, RolePermissionMapping
from apps.leaves.models import LeaveType


class Command(BaseCommand):
    help = "Seed default RBAC groups, permissions, and function permissions for the app"

    def handle(self, *args, **options):
        # 1. Seed Leave Types (Congé Types)
        self.stdout.write('Seeding leave types (types de congé)...')
        leave_types_data = [
            {
                'code': 'CA',
                'name': 'Congé Annuel',
                'description': 'Congé annuel ordinaire',
                'paid': True,
                'annual_days': 22,
                'prorata_monthly': True,
                'carry_over_years': 2,
                'exclude_weekends': True,
                'requires_approval': True
            },
            {
                'code': 'CM',
                'name': 'Congé Maladie',
                'description': 'Congé pour raison médicale',
                'paid': True,
                'annual_days': 90,
                'prorata_monthly': False,
                'carry_over_years': 0,
                'exclude_weekends': True,
                'requires_approval': False
            },
            {
                'code': 'CE',
                'name': 'Congé Exceptionnel',
                'description': 'Congé pour événements familiaux (mariage, naissance, décès)',
                'paid': True,
                'annual_days': 10,
                'prorata_monthly': False,
                'carry_over_years': 0,
                'exclude_weekends': True,
                'requires_approval': True
            },
            {
                'code': 'CM_MAT',
                'name': 'Congé Maternité',
                'description': 'Congé de maternité',
                'paid': True,
                'annual_days': 98,
                'prorata_monthly': False,
                'carry_over_years': 0,
                'exclude_weekends': False,
                'requires_approval': False
            },
            {
                'code': 'CM_PAT',
                'name': 'Congé Paternité',
                'description': 'Congé de paternité',
                'paid': True,
                'annual_days': 3,
                'prorata_monthly': False,
                'carry_over_years': 0,
                'exclude_weekends': True,
                'requires_approval': True
            },
            {
                'code': 'CSS',
                'name': 'Congé Sans Solde',
                'description': 'Congé non rémunéré',
                'paid': False,
                'annual_days': 0,
                'prorata_monthly': False,
                'carry_over_years': 0,
                'exclude_weekends': False,
                'requires_approval': True
            },
            {
                'code': 'CF',
                'name': 'Congé de Formation',
                'description': 'Congé pour formation professionnelle',
                'paid': True,
                'annual_days': 30,
                'prorata_monthly': False,
                'carry_over_years': 0,
                'exclude_weekends': True,
                'requires_approval': True
            },
        ]
        
        for lt_data in leave_types_data:
            LeaveType.objects.get_or_create(
                code=lt_data['code'],
                defaults={
                    'name': lt_data['name'],
                    'description': lt_data['description'],
                    'paid': lt_data['paid'],
                    'annual_days': lt_data['annual_days'],
                    'prorata_monthly': lt_data['prorata_monthly'],
                    'carry_over_years': lt_data['carry_over_years'],
                    'exclude_weekends': lt_data['exclude_weekends'],
                    'requires_approval': lt_data['requires_approval'],
                    'is_active': True
                }
            )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(leave_types_data)} leave types'))

        # 2. Seed Function Permissions
        self.stdout.write('Seeding function permissions...')
        functions_data = [
            # Employees module
            {'code': 'employees.view', 'name': 'View Employees', 'module': 'employees', 'description': 'Can view employee list and details'},
            {'code': 'employees.view_own', 'name': 'View Own Profile', 'module': 'employees', 'description': 'Can only view own employee profile'},
            {'code': 'employees.add', 'name': 'Add Employee', 'module': 'employees', 'description': 'Can create new employees'},
            {'code': 'employees.change', 'name': 'Edit Employee', 'module': 'employees', 'description': 'Can modify employee records'},
            {'code': 'employees.delete', 'name': 'Delete Employee', 'module': 'employees', 'description': 'Can delete employee records'},
            
            # Leaves module
            {'code': 'leaves.view', 'name': 'View Leave Requests', 'module': 'leaves', 'description': 'Can view all leave requests'},
            {'code': 'leaves.view_own', 'name': 'View Own Leaves', 'module': 'leaves', 'description': 'Can view own leave requests'},
            {'code': 'leaves.request', 'name': 'Request Leave', 'module': 'leaves', 'description': 'Can submit leave requests'},
            {'code': 'leaves.approve', 'name': 'Approve Leave', 'module': 'leaves', 'description': 'Can approve/reject leave requests'},
            {'code': 'leaves.manage_types', 'name': 'Manage Leave Types', 'module': 'leaves', 'description': 'Can create and edit leave types'},
            
            # Organization module
            {'code': 'org.view', 'name': 'View Organization', 'module': 'organization', 'description': 'Can view organizational structure'},
            {'code': 'org.manage', 'name': 'Manage Organization', 'module': 'organization', 'description': 'Can create/edit directions, divisions, services'},
            
            # Users & Roles module
            {'code': 'users.view', 'name': 'View Users', 'module': 'users', 'description': 'Can view user list'},
            {'code': 'users.manage', 'name': 'Manage Users', 'module': 'users', 'description': 'Can create/edit/delete users'},
            {'code': 'roles.view', 'name': 'View Roles', 'module': 'roles', 'description': 'Can view roles and permissions'},
            {'code': 'roles.manage', 'name': 'Manage Roles', 'module': 'roles', 'description': 'Can create/edit/delete roles'},
            
            # Dashboard module
            {'code': 'dashboard.view', 'name': 'View Dashboard', 'module': 'dashboard', 'description': 'Can access admin dashboard'},
            {'code': 'documents.view', 'name': 'View Documents', 'module': 'documents', 'description': 'Can view and download documents'},
            {'code': 'documents.upload', 'name': 'Upload Documents', 'module': 'documents', 'description': 'Can upload documents'},
        ]
        
        for func_data in functions_data:
            FunctionPermission.objects.get_or_create(
                code=func_data['code'],
                defaults={
                    'name': func_data['name'],
                    'module': func_data['module'],
                    'description': func_data['description'],
                    'is_active': True
                }
            )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(functions_data)} function permissions'))

        # 2. Create Groups and RoleDefinitions
        self.stdout.write('Creating roles...')
        
        # IT Admin role (system role with full permissions)
        it_admin_group, _ = Group.objects.get_or_create(name='IT Admin')
        it_admin_role, _ = RoleDefinition.objects.get_or_create(
            group=it_admin_group,
            defaults={
                'description': 'System administrator with full access',
                'is_system_role': True
            }
        )
        # Assign all function permissions to IT Admin
        all_functions = FunctionPermission.objects.filter(is_active=True)
        RolePermissionMapping.objects.filter(role=it_admin_role).delete()
        RolePermissionMapping.objects.bulk_create([
            RolePermissionMapping(role=it_admin_role, function=f) for f in all_functions
        ])
        self.stdout.write(self.style.SUCCESS('  ✓ IT Admin role with all permissions'))

        # HR Admin role
        hr_admin_group, _ = Group.objects.get_or_create(name='HR Admin')
        hr_admin_role, _ = RoleDefinition.objects.get_or_create(
            group=hr_admin_group,
            defaults={
                'description': 'HR administrator - manages employees and leaves',
                'is_system_role': True
            }
        )
        hr_function_codes = [
            'employees.view', 'employees.add', 'employees.change',
            'leaves.view', 'leaves.approve', 'leaves.manage_types',
            'org.view', 'dashboard.view', 'documents.view', 'documents.upload'
        ]
        hr_functions = FunctionPermission.objects.filter(code__in=hr_function_codes, is_active=True)
        RolePermissionMapping.objects.filter(role=hr_admin_role).delete()
        RolePermissionMapping.objects.bulk_create([
            RolePermissionMapping(role=hr_admin_role, function=f) for f in hr_functions
        ])
        self.stdout.write(self.style.SUCCESS('  ✓ HR Admin role'))

        # Normal User role (default for regular employees)
        normal_user_group, _ = Group.objects.get_or_create(name='Normal User')
        normal_user_role, _ = RoleDefinition.objects.get_or_create(
            group=normal_user_group,
            defaults={
                'description': 'Regular employee - can view own profile and submit leave requests',
                'is_system_role': True
            }
        )
        normal_user_function_codes = [
            'employees.view_own',
            'leaves.view_own',
            'leaves.request',
            'documents.view'
        ]
        normal_user_functions = FunctionPermission.objects.filter(code__in=normal_user_function_codes, is_active=True)
        RolePermissionMapping.objects.filter(role=normal_user_role).delete()
        RolePermissionMapping.objects.bulk_create([
            RolePermissionMapping(role=normal_user_role, function=f) for f in normal_user_functions
        ])
        self.stdout.write(self.style.SUCCESS('  ✓ Normal User role'))

        # 3. Assign Django model permissions to groups
        models = [Employee, Direction, Division, Service, Grade, Position]
        content_types = {m.__name__: ContentType.objects.get_for_model(m) for m in models}

        def perms_for(model_cls, codenames):
            ct = content_types[model_cls.__name__]
            return list(Permission.objects.filter(content_type=ct, codename__in=codenames))

        # IT Admin: all permissions
        all_employees_app_perms = Permission.objects.filter(content_type__in=content_types.values())
        it_admin_group.permissions.set(all_employees_app_perms)

        # HR Admin: manage employees, view reference data
        hr_perms = []
        hr_perms += perms_for(Employee, ["view_employee", "add_employee", "change_employee"])
        for ref_model in [Direction, Division, Service, Grade, Position]:
            hr_perms += perms_for(ref_model, [f"view_{ref_model.__name__.lower()}"])
        hr_admin_group.permissions.set(hr_perms)

        # Normal User: view employees only
        normal_user_perms = perms_for(Employee, ["view_employee"])
        normal_user_group.permissions.set(normal_user_perms)

        self.stdout.write(self.style.SUCCESS("\n✅ Roles, function permissions, and Django permissions seeded successfully"))
        self.stdout.write(self.style.NOTICE("Roles created: IT Admin, HR Admin, Normal User"))
