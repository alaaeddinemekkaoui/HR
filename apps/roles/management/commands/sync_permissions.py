"""
Management command to auto-sync permissions from Django models to FunctionPermission.
Also auto-assigns all permissions to IT Admin and HR groups.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.roles.models import FunctionPermission, RoleDefinition, RolePermissionMapping


class Command(BaseCommand):
    help = 'Sync Django permissions to FunctionPermission and auto-assign to IT Admin & HR groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
        
        # Get or create IT Admin and HR groups
        it_admin_group, _ = Group.objects.get_or_create(name='IT Admin')
        hr_group, _ = Group.objects.get_or_create(name='HR')
        
        self.stdout.write(self.style.SUCCESS(f'✅ Groups: IT Admin (id={it_admin_group.id}), HR (id={hr_group.id})'))
        
        # Get or create RoleDefinitions for these groups
        it_admin_role, created = RoleDefinition.objects.get_or_create(
            group=it_admin_group,
            defaults={
                'description': 'IT Administrators with full system access',
                'is_system_role': True
            }
        )
        if created and not dry_run:
            self.stdout.write(self.style.SUCCESS(f'  ➕ Created RoleDefinition for IT Admin'))
        
        hr_role, created = RoleDefinition.objects.get_or_create(
            group=hr_group,
            defaults={
                'description': 'HR team with full employee and leave management access',
                'is_system_role': True
            }
        )
        if created and not dry_run:
            self.stdout.write(self.style.SUCCESS(f'  ➕ Created RoleDefinition for HR'))
        
        # Sync Django permissions to FunctionPermission
        self.stdout.write('\n📋 Syncing Django permissions to FunctionPermission...')
        
        # Relevant apps to sync
        relevant_apps = ['employees', 'leaves', 'roles', 'authentication', 'admin_dashboard']
        
        synced_count = 0
        skipped_count = 0
        
        for app_label in relevant_apps:
            content_types = ContentType.objects.filter(app_label=app_label)
            
            for ct in content_types:
                model_name = ct.model
                permissions = Permission.objects.filter(content_type=ct)
                
                for perm in permissions:
                    # Create code like: employees.employee.add, leaves.leavetype.change, etc.
                    code = f"{app_label}.{model_name}.{perm.codename.split('_')[0]}"
                    
                    # Human-readable name
                    name = f"{perm.name} ({model_name})"
                    
                    # Check if already exists
                    if FunctionPermission.objects.filter(code=code).exists():
                        skipped_count += 1
                        continue
                    
                    if not dry_run:
                        FunctionPermission.objects.create(
                            code=code,
                            name=name,
                            description=f"Permission: {perm.name}",
                            module=app_label,
                            is_active=True
                        )
                    
                    self.stdout.write(f'  ➕ {code}: {name}')
                    synced_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Synced {synced_count} new permissions, skipped {skipped_count} existing'))
        
        # Assign ALL permissions to IT Admin
        self.stdout.write('\n🔐 Assigning permissions to IT Admin (full access)...')
        all_functions = FunctionPermission.objects.filter(is_active=True)
        it_admin_assigned = 0
        
        for func in all_functions:
            if not RolePermissionMapping.objects.filter(role=it_admin_role, function=func).exists():
                if not dry_run:
                    RolePermissionMapping.objects.create(role=it_admin_role, function=func)
                it_admin_assigned += 1
        
        # Also assign all Django permissions directly to IT Admin group
        if not dry_run:
            all_perms = Permission.objects.all()
            it_admin_group.permissions.set(all_perms)
        
        self.stdout.write(self.style.SUCCESS(f'✅ IT Admin: {it_admin_assigned} new function mappings + all Django permissions'))
        
        # Assign HR-relevant permissions to HR group (exclude IT Admin specific ones)
        self.stdout.write('\n👥 Assigning permissions to HR group (employee & leave management)...')
        hr_modules = ['employees', 'leaves']
        hr_functions = FunctionPermission.objects.filter(module__in=hr_modules, is_active=True)
        hr_assigned = 0
        
        for func in hr_functions:
            if not RolePermissionMapping.objects.filter(role=hr_role, function=func).exists():
                if not dry_run:
                    RolePermissionMapping.objects.create(role=hr_role, function=func)
                hr_assigned += 1
        
        # Assign Django permissions for HR modules
        if not dry_run:
            hr_perms = Permission.objects.filter(
                content_type__app_label__in=hr_modules
            )
            hr_group.permissions.add(*hr_perms)
        
        self.stdout.write(self.style.SUCCESS(f'✅ HR: {hr_assigned} new function mappings + employee/leave Django permissions'))
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🎉 Permission sync complete!'))
        self.stdout.write(f'   IT Admin: Full system access (priority group)')
        self.stdout.write(f'   HR: Employee & Leave management access')
        self.stdout.write('='*60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  This was a DRY RUN. Run without --dry-run to apply changes.'))
