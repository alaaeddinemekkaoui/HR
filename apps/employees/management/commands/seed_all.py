"""
Management command to seed all data in the correct order
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Seeds all application data in the correct order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-iav',
            action='store_true',
            help='Skip IAV organizational data seeding',
        )
        parser.add_argument(
            '--skip-admin',
            action='store_true',
            help='Skip admin user creation',
        )
        parser.add_argument(
            '--skip-roles',
            action='store_true',
            help='Skip roles and permissions seeding',
        )
        parser.add_argument(
            '--skip-samples',
            action='store_true',
            help='Skip sample employee data',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('SEEDING ALL APPLICATION DATA'))
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write()

        # Step 1: Seed IAV organizational structure (grades, positions, org units)
        if not options['skip_iav']:
            self.stdout.write(self.style.HTTP_INFO('Step 1/4: Seeding IAV organizational data...'))
            self.stdout.write('-' * 80)
            try:
                call_command('seed_iav_data')
                self.stdout.write(self.style.SUCCESS('✅ IAV data seeded successfully\n'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to seed IAV data: {e}\n'))
                return
        else:
            self.stdout.write(self.style.WARNING('⏭️  Skipping IAV data seeding\n'))

        # Step 2: Create admin users
        if not options['skip_admin']:
            self.stdout.write(self.style.HTTP_INFO('Step 2/4: Creating admin users...'))
            self.stdout.write('-' * 80)
            try:
                call_command('seed_admin_user')
                self.stdout.write(self.style.SUCCESS('✅ Admin users created successfully\n'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to create admin users: {e}\n'))
                return
        else:
            self.stdout.write(self.style.WARNING('⏭️  Skipping admin user creation\n'))

        # Step 3: Seed roles and permissions
        if not options['skip_roles']:
            self.stdout.write(self.style.HTTP_INFO('Step 3/4: Seeding roles and permissions...'))
            self.stdout.write('-' * 80)
            try:
                call_command('seed_roles')
                self.stdout.write(self.style.SUCCESS('✅ Roles and permissions seeded successfully\n'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to seed roles: {e}\n'))
                return
        else:
            self.stdout.write(self.style.WARNING('⏭️  Skipping roles seeding\n'))

        # Step 4: Seed sample employees (LAST - after roles exist)
        if not options['skip_samples']:
            self.stdout.write(self.style.HTTP_INFO('Step 4/4: Seeding sample employee data...'))
            self.stdout.write('-' * 80)
            try:
                call_command('seed_sample_employees')
                self.stdout.write(self.style.SUCCESS('✅ Sample employees seeded successfully\n'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to seed sample employees: {e}\n'))
                return
        else:
            self.stdout.write(self.style.WARNING('⏭️  Skipping sample employee seeding\n'))

        # Summary
        self.stdout.write()
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('🎉 ALL DATA SEEDED SUCCESSFULLY!'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write()
        self.stdout.write(self.style.HTTP_INFO('📋 Login Credentials:'))
        self.stdout.write(self.style.WARNING('   IT Admin:  username: admin    password: admin123'))
        self.stdout.write(self.style.WARNING('   HR Admin:  username: rh       password: rh12345'))
        self.stdout.write(self.style.WARNING('   Employees: password for all:  rabat2025'))
        self.stdout.write()
        self.stdout.write(self.style.HTTP_INFO('🌐 Access the application at: http://localhost:8000'))
        self.stdout.write()
