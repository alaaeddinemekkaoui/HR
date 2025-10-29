from django.core.management.base import BaseCommand
from apps.roles.models import FunctionPermission, RolePermissionMapping, RoleDefinition


class Command(BaseCommand):
    help = 'Seed signature permissions into the system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('🔐 Seeding signature permissions...'))
        
        # Define signature functions
        signature_functions = [
            ('signature.view', 'View Signatures', 'Electronic Signatures'),
            ('signature.sign', 'Sign Documents', 'Electronic Signatures'),
            ('signature.request', 'Request Signatures', 'Electronic Signatures'),
            ('signature.reject', 'Reject Signature Requests', 'Electronic Signatures'),
            ('signature.verify', 'Verify Signature Integrity', 'Electronic Signatures'),
            ('signature.admin', 'Manage Signature System', 'Electronic Signatures'),
        ]
        
        created_count = 0
        for perm_name, description, category in signature_functions:
            func, created = FunctionPermission.objects.get_or_create(
                code=perm_name,
                defaults={
                    'name': description,
                    'description': description,
                    'module': category
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✓ Created function: {perm_name}")
            else:
                self.stdout.write(f"  → Function exists: {perm_name}")
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Created {created_count} new signature functions'))
        
        # Assign permissions to roles
        self.stdout.write(self.style.WARNING('\n📋 Assigning permissions to roles...'))
        
        try:
            # IT Admin gets all signature permissions
            it_admin = RoleDefinition.objects.get(group__name='IT Admin')
            it_admin_assigned = 0
            for perm_name, _, _ in signature_functions:
                func = FunctionPermission.objects.get(code=perm_name)
                role_perm, created = RolePermissionMapping.objects.get_or_create(
                    role=it_admin,
                    function=func
                )
                if created:
                    it_admin_assigned += 1
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ IT Admin: {it_admin_assigned} new permissions'))
        except RoleDefinition.DoesNotExist:
            self.stdout.write(self.style.ERROR('  ✗ IT Admin role not found'))
        
        try:
            # HR Admin gets signature permissions (except admin)
            hr_admin = RoleDefinition.objects.get(group__name='HR Admin')
            hr_admin_assigned = 0
            hr_perms = [
                'signature.view',
                'signature.sign',
                'signature.request',
                'signature.verify'
            ]
            for perm_name in hr_perms:
                func = FunctionPermission.objects.get(code=perm_name)
                role_perm, created = RolePermissionMapping.objects.get_or_create(
                    role=hr_admin,
                    function=func
                )
                if created:
                    hr_admin_assigned += 1
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ HR Admin: {hr_admin_assigned} new permissions'))
        except RoleDefinition.DoesNotExist:
            self.stdout.write(self.style.ERROR('  ✗ HR Admin role not found'))
        
        try:
            # Managers get basic signature permissions
            manager = RoleDefinition.objects.get(group__name='Manager')
            manager_assigned = 0
            manager_perms = [
                'signature.view',
                'signature.sign',
            ]
            for perm_name in manager_perms:
                func = FunctionPermission.objects.get(code=perm_name)
                role_perm, created = RolePermissionMapping.objects.get_or_create(
                    role=manager,
                    function=func
                )
                if created:
                    manager_assigned += 1
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Manager: {manager_assigned} new permissions'))
        except RoleDefinition.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ⚠ Manager role not found (skipping)'))
        
        try:
            # All employees get sign permission
            hr_view = RoleDefinition.objects.get(group__name='HR View')
            view_assigned = 0
            view_perms = ['signature.view', 'signature.sign']
            for perm_name in view_perms:
                func = FunctionPermission.objects.get(code=perm_name)
                role_perm, created = RolePermissionMapping.objects.get_or_create(
                    role=hr_view,
                    function=func
                )
                if created:
                    view_assigned += 1
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ HR View: {view_assigned} new permissions'))
        except RoleDefinition.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ⚠ HR View role not found (skipping)'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Signature permissions setup complete!\n'))
        
        # Display summary
        self.stdout.write('📊 Permission Summary:')
        self.stdout.write('  • IT Admin: Full signature system access')
        self.stdout.write('  • HR Admin: View, sign, request, verify')
        self.stdout.write('  • Manager: View and sign')
        self.stdout.write('  • HR View: View and sign')
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  1. Navigate to /signatures/my-requests/ to see signature dashboard')
        self.stdout.write('  2. Create deployments/leave requests to trigger signature requests')
        self.stdout.write('  3. Check docs/SIGNATURE_QUICK_START.md for integration guide')
