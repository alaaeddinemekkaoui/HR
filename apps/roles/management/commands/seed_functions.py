from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.roles.models import RoleDefinition, FunctionPermission, RolePermissionMapping


class Command(BaseCommand):
    help = "Seed function permissions and map them to roles"

    def handle(self, *args, **options):
        # Define available functions - organized by category
        functions = [
            # Employee Management
            ('employees.view', 'View Employees', 'employees', 'View employee list and details'),
            ('employees.add', 'Add Employees', 'employees', 'Create new employees'),
            ('employees.edit', 'Edit Employees', 'employees', 'Modify existing employees'),
            ('employees.delete', 'Delete Employees', 'employees', 'Remove employees'),
            ('employees.export', 'Export Employees', 'employees', 'Export employee data'),
            ('employees.admin', 'Employee Admin', 'employees', 'Full employee management access'),
            
            # Grades & Positions Management
            ('grades.view', 'View Grades', 'grades', 'View grade definitions'),
            ('grades.manage', 'Manage Grades', 'grades', 'Create, edit, and delete grades'),
            ('positions.view', 'View Positions', 'grades', 'View position definitions'),
            ('positions.manage', 'Manage Positions', 'grades', 'Create, edit, and delete positions'),
            
            # Organization Structure
            ('org.view', 'View Organization', 'organization', 'View services, directions, divisions'),
            ('org.manage', 'Manage Organization', 'organization', 'Manage organizational structure'),
            
            # Career Progression
            ('progression.view', 'View Progressions', 'progression', 'View career progression records'),
            ('progression.add', 'Add Progressions', 'progression', 'Create career progression records'),
            ('progression.edit', 'Edit Progressions', 'progression', 'Modify progression records'),
            ('progression.delete', 'Delete Progressions', 'progression', 'Remove progression records'),
            
            # Deployments - Forfaitaire
            ('deployment_forfaitaire.view', 'View Forfaitaire Deployments', 'deployments', 'View forfaitaire deployment requests'),
            ('deployment_forfaitaire.create', 'Create Forfaitaire Deployments', 'deployments', 'Create forfaitaire deployment requests'),
            ('deployment_forfaitaire.edit', 'Edit Forfaitaire Deployments', 'deployments', 'Modify forfaitaire deployments'),
            ('deployment_forfaitaire.delete', 'Delete Forfaitaire Deployments', 'deployments', 'Remove forfaitaire deployments'),
            ('deployment_forfaitaire.approve', 'Approve Forfaitaire Deployments', 'deployments', 'Approve/reject forfaitaire requests'),
            ('deployment_forfaitaire.sign', 'Sign Forfaitaire Deployments', 'deployments', 'Sign approved forfaitaire deployments'),
            ('deployment_forfaitaire.admin', 'Forfaitaire Admin', 'deployments', 'Full forfaitaire deployment management'),
            
            # Deployments - Real
            ('deployment_real.view', 'View Real Deployments', 'deployments', 'View real deployment requests'),
            ('deployment_real.create', 'Create Real Deployments', 'deployments', 'Create real deployment requests'),
            ('deployment_real.edit', 'Edit Real Deployments', 'deployments', 'Modify real deployments'),
            ('deployment_real.delete', 'Delete Real Deployments', 'deployments', 'Remove real deployments'),
            ('deployment_real.approve', 'Approve Real Deployments', 'deployments', 'Approve/reject real requests'),
            ('deployment_real.sign', 'Sign Real Deployments', 'deployments', 'Sign approved real deployments'),
            ('deployment_real.admin', 'Real Deployment Admin', 'deployments', 'Full real deployment management'),
            
            # Deployments - Ordre de Mission
            ('deployment_ordre.view', 'View Ordre de Mission', 'deployments', 'View ordre de mission requests'),
            ('deployment_ordre.create', 'Create Ordre de Mission', 'deployments', 'Create ordre de mission requests'),
            ('deployment_ordre.edit', 'Edit Ordre de Mission', 'deployments', 'Modify ordre de mission'),
            ('deployment_ordre.delete', 'Delete Ordre de Mission', 'deployments', 'Remove ordre de mission'),
            ('deployment_ordre.approve', 'Approve Ordre de Mission', 'deployments', 'Approve/reject ordre requests'),
            ('deployment_ordre.sign', 'Sign Ordre de Mission', 'deployments', 'Sign approved ordre de mission'),
            
            # Leaves Management
            ('leaves.view', 'View Leaves', 'leaves', 'View leave requests and balances'),
            ('leaves.request', 'Request Leaves', 'leaves', 'Submit leave requests'),
            ('leaves.edit', 'Edit Leaves', 'leaves', 'Modify leave requests'),
            ('leaves.delete', 'Delete Leaves', 'leaves', 'Cancel/remove leave requests'),
            ('leaves.approve', 'Approve Leaves', 'leaves', 'Approve or reject leave requests'),
            ('leaves.manage_types', 'Manage Leave Types', 'leaves', 'Create and configure leave types'),
            ('leaves.admin', 'Leave Admin', 'leaves', 'Full leave management access'),
            
            # Documents Management
            ('documents.view', 'View Documents', 'documents', 'View and download documents'),
            ('documents.upload', 'Upload Documents', 'documents', 'Upload new documents'),
            ('documents.edit', 'Edit Documents', 'documents', 'Modify document metadata'),
            ('documents.delete', 'Delete Documents', 'documents', 'Remove documents'),
            ('documents.admin', 'Document Admin', 'documents', 'Full document management access'),
            
            # User Management
            ('users.view', 'View Users', 'users', 'View user accounts'),
            ('users.add', 'Add Users', 'users', 'Create new user accounts'),
            ('users.edit', 'Edit Users', 'users', 'Modify user accounts'),
            ('users.delete', 'Delete Users', 'users', 'Remove user accounts'),
            ('users.assign_roles', 'Assign User Roles', 'users', 'Assign groups/roles to users'),
            ('users.reset_passwords', 'Reset User Passwords', 'users', 'Reset user passwords'),
            ('users.admin', 'User Admin', 'users', 'Full user management access'),
            
            # Role Management
            ('roles.view', 'View Roles', 'roles', 'View role definitions'),
            ('roles.add', 'Add Roles', 'roles', 'Create new roles'),
            ('roles.edit', 'Edit Roles', 'roles', 'Modify existing roles'),
            ('roles.delete', 'Delete Roles', 'roles', 'Remove roles'),
            ('roles.assign_permissions', 'Assign Role Permissions', 'roles', 'Assign functions to roles'),
            ('roles.admin', 'Role Admin', 'roles', 'Full role management access'),
            
            # Notifications
            ('notifications.view', 'View Notifications', 'notifications', 'View notifications'),
            ('notifications.send', 'Send Notifications', 'notifications', 'Send notifications to users'),
            ('notifications.admin', 'Notification Admin', 'notifications', 'Full notification management'),
            
            # Dashboard & Reports
            ('dashboard.access', 'Access Dashboard', 'dashboard', 'View admin dashboard'),
            ('dashboard.statistics', 'View Statistics', 'dashboard', 'View statistical data'),
            ('reports.view', 'View Reports', 'reports', 'Access reports'),
            ('reports.generate', 'Generate Reports', 'reports', 'Create and export reports'),
            ('reports.admin', 'Report Admin', 'reports', 'Full reporting access'),
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
                # Full system access
                'employees.view', 'employees.add', 'employees.edit', 'employees.delete', 'employees.export', 'employees.admin',
                'grades.view', 'grades.manage', 'positions.view', 'positions.manage',
                'org.view', 'org.manage',
                'progression.view', 'progression.add', 'progression.edit', 'progression.delete',
                'deployment_forfaitaire.view', 'deployment_forfaitaire.create', 'deployment_forfaitaire.edit', 
                'deployment_forfaitaire.delete', 'deployment_forfaitaire.approve', 'deployment_forfaitaire.sign', 'deployment_forfaitaire.admin',
                'deployment_real.view', 'deployment_real.create', 'deployment_real.edit', 
                'deployment_real.delete', 'deployment_real.approve', 'deployment_real.sign', 'deployment_real.admin',
                'deployment_ordre.view', 'deployment_ordre.create', 'deployment_ordre.edit', 
                'deployment_ordre.delete', 'deployment_ordre.approve', 'deployment_ordre.sign',
                'leaves.view', 'leaves.request', 'leaves.edit', 'leaves.delete', 'leaves.approve', 'leaves.manage_types', 'leaves.admin',
                'documents.view', 'documents.upload', 'documents.edit', 'documents.delete', 'documents.admin',
                'users.view', 'users.add', 'users.edit', 'users.delete', 'users.assign_roles', 'users.reset_passwords', 'users.admin',
                'roles.view', 'roles.add', 'roles.edit', 'roles.delete', 'roles.assign_permissions', 'roles.admin',
                'notifications.view', 'notifications.send', 'notifications.admin',
                'dashboard.access', 'dashboard.statistics', 'reports.view', 'reports.generate', 'reports.admin',
            ],
            'HR Admin': [
                # HR management with deployment admin
                'employees.view', 'employees.add', 'employees.edit', 'employees.delete', 'employees.export', 'employees.admin',
                'grades.view', 'grades.manage', 'positions.view', 'positions.manage',
                'org.view', 'org.manage',
                'progression.view', 'progression.add', 'progression.edit', 'progression.delete',
                'deployment_forfaitaire.view', 'deployment_forfaitaire.create', 'deployment_forfaitaire.edit', 
                'deployment_forfaitaire.delete', 'deployment_forfaitaire.approve', 'deployment_forfaitaire.sign', 'deployment_forfaitaire.admin',
                'deployment_real.view', 'deployment_real.create', 'deployment_real.edit', 
                'deployment_real.delete', 'deployment_real.approve', 'deployment_real.sign', 'deployment_real.admin',
                'deployment_ordre.view', 'deployment_ordre.create', 'deployment_ordre.edit', 
                'deployment_ordre.delete', 'deployment_ordre.approve', 'deployment_ordre.sign',
                'leaves.view', 'leaves.request', 'leaves.edit', 'leaves.delete', 'leaves.approve', 'leaves.manage_types', 'leaves.admin',
                'documents.view', 'documents.upload', 'documents.edit', 'documents.delete', 'documents.admin',
                'roles.view',
                'notifications.view', 'notifications.send',
                'dashboard.access', 'dashboard.statistics', 'reports.view', 'reports.generate',
            ],
            'HR Edit': [
                # Can edit employees and view deployments
                'employees.view', 'employees.add', 'employees.edit', 'employees.export',
                'grades.view', 'positions.view',
                'org.view',
                'progression.view', 'progression.add',
                'deployment_ordre.view', 'deployment_ordre.create',
                'leaves.view', 'leaves.request',
                'documents.view', 'documents.upload',
                'notifications.view',
                'reports.view',
            ],
            'HR Add': [
                # Can add employees and create ordre de mission
                'employees.view', 'employees.add',
                'grades.view', 'positions.view',
                'org.view',
                'deployment_ordre.view', 'deployment_ordre.create',
                'leaves.view', 'leaves.request',
                'documents.view',
                'notifications.view',
            ],
            'HR View': [
                # Read-only access
                'employees.view',
                'grades.view', 'positions.view',
                'org.view',
                'progression.view',
                'deployment_ordre.view',
                'leaves.view',
                'documents.view',
                'notifications.view',
            ],
            'Manager': [
                # Can approve leaves and deployments for their team
                'employees.view',
                'grades.view', 'positions.view',
                'org.view',
                'deployment_ordre.view', 'deployment_ordre.create', 'deployment_ordre.approve',
                'leaves.view', 'leaves.request', 'leaves.approve',
                'documents.view',
                'notifications.view',
                'dashboard.access',
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
