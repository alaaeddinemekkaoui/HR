from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from apps.employees.models import Employee, Direction, Position, Grade


class Command(BaseCommand):
    help = 'Create admin users (IT Admin and HR Admin) with their respective groups and employee profiles'

    def handle(self, *args, **kwargs):
        # Create IT Admin group
        it_admin_group, _ = Group.objects.get_or_create(name='IT Admin')
        # Create HR Admin group
        hr_admin_group, _ = Group.objects.get_or_create(name='HR Admin')
        
        # ===== IT ADMIN USER =====
        self.stdout.write('\nCreating IT Admin user...')
        
        # Check if admin user already exists
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('  ! Admin user already exists'))
            admin_user = User.objects.get(username='admin')
        else:
            # Create superuser
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@iav.ac.ma',
                password='admin123',
                first_name='Admin',
                last_name='System'
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Created superuser: admin'))
        
        # Add to IT Admin group
        if not admin_user.groups.filter(name='IT Admin').exists():
            admin_user.groups.add(it_admin_group)
            self.stdout.write(self.style.SUCCESS('  ✓ Added admin to IT Admin group'))
        
        # Create employee profile if doesn't exist
        if not hasattr(admin_user, 'employee_profile'):
            try:
                # Get required references
                sg = Direction.objects.get(code='SG')
                position_dir = Position.objects.get(code='DIR')
                grade_ing_chef = Grade.objects.get(code='ING_CHEF')
                
                employee = Employee.objects.create(
                    user=admin_user,
                    first_name='Admin',
                    last_name='System',
                    cin='ADMIN001',
                    email='admin@iav.ac.ma',
                    phone='0612345678',
                    date_of_birth='1980-01-01',
                    employee_id='ADMIN001',
                    ppr='ADMIN-PPR',
                    direction=sg,
                    position=position_dir,
                    grade=grade_ing_chef,
                    echelle=11,
                    echelon=10,
                    status='active',
                    contract_type='titulaire',
                    hire_date='2020-01-01',
                )
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created employee profile: {employee.full_name}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ! Could not create employee profile: {str(e)}'))
                self.stdout.write(self.style.WARNING('    Run seed_iav_data first to create required organizational structure'))
        else:
            self.stdout.write('  - Employee profile already exists')
        
        # ===== HR ADMIN USER =====
        self.stdout.write('\nCreating HR Admin user...')
        
        # Check if RH user already exists
        if User.objects.filter(username='rh').exists():
            self.stdout.write(self.style.WARNING('  ! RH user already exists'))
            rh_user = User.objects.get(username='rh')
        else:
            # Create staff user (not superuser)
            rh_user = User.objects.create_user(
                username='rh',
                email='rh@iav.ac.ma',
                password='rh12345',
                first_name='RH',
                last_name='Admin',
                is_staff=True  # Can access admin site
            )
            self.stdout.write(self.style.SUCCESS('  ✓ Created staff user: rh'))
        
        # Add to HR Admin group
        if not rh_user.groups.filter(name='HR Admin').exists():
            rh_user.groups.add(hr_admin_group)
            self.stdout.write(self.style.SUCCESS('  ✓ Added rh to HR Admin group'))
        
        # Create employee profile if doesn't exist
        if not hasattr(rh_user, 'employee_profile'):
            try:
                # Get required references
                dg = Direction.objects.get(code='DG')
                position_dir = Position.objects.get(code='DIR')
                grade_ing_chef = Grade.objects.get(code='ING_CHEF')
                
                employee = Employee.objects.create(
                    user=rh_user,
                    first_name='RH',
                    last_name='Admin',
                    cin='RH001',
                    email='rh@iav.ac.ma',
                    phone='0612345679',
                    date_of_birth='1985-01-01',
                    employee_id='RH001',
                    ppr='RH-PPR',
                    direction=dg,
                    position=position_dir,
                    grade=grade_ing_chef,
                    echelle=10,
                    echelon=8,
                    status='active',
                    contract_type='titulaire',
                    hire_date='2021-01-01',
                )
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created employee profile: {employee.full_name}'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ! Could not create employee profile: {str(e)}'))
                self.stdout.write(self.style.WARNING('    Run seed_iav_data first to create required organizational structure'))
        else:
            self.stdout.write('  - Employee profile already exists')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n✓ Admin users setup completed!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('\nIT Admin (Superuser):')
        self.stdout.write(f'  Username: admin')
        self.stdout.write(f'  Password: admin123')
        self.stdout.write(f'  Email: admin@iav.ac.ma')
        self.stdout.write(f'  Group: IT Admin')
        self.stdout.write('\nHR Admin (Staff):')
        self.stdout.write(f'  Username: rh')
        self.stdout.write(f'  Password: rh12345')
        self.stdout.write(f'  Email: rh@iav.ac.ma')
        self.stdout.write(f'  Group: HR Admin')
