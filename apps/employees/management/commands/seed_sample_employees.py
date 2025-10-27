from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date
import random
from apps.employees.models import Direction, Division, Service, Grade, Position, Employee, Departement, Filiere

class Command(BaseCommand):
    help = 'Seed a set of sample employees and auto-provision user accounts (password: rabat2025)'

    def handle(self, *args, **options):
        # Ensure org and taxonomy exist
        if Direction.objects.count() == 0 or Grade.objects.count() == 0 or Position.objects.count() == 0:
            self.stdout.write(self.style.WARNING('Org/Grades/Positions not found. Run seed_iav_data first.'))
            return

        dg = Direction.objects.get(code='DG')
        sg = Direction.objects.get(code='SG')
        de = Direction.objects.get(code='DE')
        
        # Get divisions and services to demonstrate different assignment patterns
        div_scol = Division.objects.filter(code='SCOL').first()
        div_adm = Division.objects.filter(code='ADM').first()
        
        # Services
        it_service = Service.objects.filter(code='IT').first()  # IT directly under SG (no division)
        inscr_service = Service.objects.filter(code='INSCR').first()  # Under Division SCOL
        cour_service = Service.objects.filter(code='COUR').first()  # Under Division ADM
        
        # Get départements and filières
        dept_info = Departement.objects.filter(code='INFO').first()
        dept_agro = Departement.objects.filter(code='AGRO').first()
        dept_genie = Departement.objects.filter(code='GENIE').first()
        filiere_gl = Filiere.objects.filter(code='GL').first()
        filiere_ia = Filiere.objects.filter(code='IA').first()
        filiere_pa = Filiere.objects.filter(code='PA').first()

        grades = {g.code: g for g in Grade.objects.all()}
        positions = {p.code: p for p in Position.objects.all()}

        today = timezone.now().date()
        samples = [
            # Pattern 1: Direction only (no division, no service) - High-level positions
            # first_name, last_name, email, cin, direction, division, service, dept, filiere, position, grade, echelle
            ('Ahmed', 'El Mansouri', 'ahmed.mansouri@iav.ac.ma', 'CIN10001', dg, None, None, None, None, positions.get('DIR'), grades.get('ING_CHEF'), 11),
            
            # Pattern 2: Direction + Service (no division) - IT Service directly under SG
            ('Youssef', 'Bennani', 'youssef.bennani@iav.ac.ma', 'CIN10003', sg, None, it_service, None, None, positions.get('CHEF_SRV'), grades.get('ING_PRIN'), 10),
            ('Karim', 'Benjelloun', 'karim.benjelloun@iav.ac.ma', 'CIN10007', sg, None, it_service, None, None, positions.get('ING'), grades.get('ING'), 9),
            ('Rachid', 'Alami', 'rachid.alami@iav.ac.ma', 'CIN10009', sg, None, it_service, None, None, positions.get('TECH'), grades.get('TECH_1G'), 8),
            
            # Pattern 3: Direction + Division (no service) - Division-level positions
            ('Imane', 'Fassi', 'imane.fassi@iav.ac.ma', 'CIN10008', sg, div_adm, None, None, None, positions.get('CHEF_DIV'), grades.get('ING_PRIN'), 10),
            
            # Pattern 4: Direction + Division + Service - Traditional hierarchy
            ('Fatima', 'Zahra', 'fatima.zahra@iav.ac.ma', 'CIN10002', de, div_scol, inscr_service, None, None, positions.get('CHEF_SRV'), grades.get('ING_PRIN'), 10),
            ('Laila', 'Chraibi', 'laila.chraibi@iav.ac.ma', 'CIN10010', sg, div_adm, cour_service, None, None, positions.get('AG_ADM'), grades.get('AG_ADM'), 6),
            
            # Pattern 5: Direction + Département + Filière - Academic structure
            ('Salma', 'Haddad', 'salma.haddad@iav.ac.ma', 'CIN10004', de, None, None, dept_info, filiere_gl, positions.get('CHEF_FIL'), grades.get('PROF_AGREGE'), 11),
            ('Hassan', 'Amrani', 'hassan.amrani@iav.ac.ma', 'CIN10005', de, None, None, dept_agro, None, positions.get('CHEF_DEPT'), grades.get('ING_PRIN'), 10),
            ('Nadia', 'Tazi', 'nadia.tazi@iav.ac.ma', 'CIN10006', de, None, None, dept_info, filiere_ia, positions.get('PROF'), grades.get('PROF_AGREGE'), 10),
            ('Omar', 'Benkirane', 'omar.benkirane@iav.ac.ma', 'CIN10011', de, None, None, dept_genie, None, positions.get('PROF'), grades.get('ING_PRIN'), 9),
            
            # Pattern 6: Direction + Département (no filière) - Department-level positions
            ('Zineb', 'Kadiri', 'zineb.kadiri@iav.ac.ma', 'CIN10012', de, None, None, dept_info, None, positions.get('SEC'), grades.get('ADM_1G'), 7),
        ]

        created = 0
        for first, last, email, cin, direction, division, service, dept, filiere, position, grade, echelle in samples:
            if not position or not grade:
                self.stdout.write(self.style.WARNING(f'  Skipping {first} {last}: missing position or grade'))
                continue
                
            emp, was_created = Employee.objects.update_or_create(
                email=email,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'cin': cin,
                    'phone': '0612345678',
                    'date_of_birth': date(1985, 5, 15),
                    'address': 'Rabat, Morocco',
                    'employee_id': cin,
                    'ppr': f'PPR{cin[-5:]}',
                    'direction': direction,
                    'division': division,
                    'service': service,
                    'departement': dept,
                    'filiere': filiere,
                    'position': position,
                    'grade': grade,
                    'echelle': echelle,
                    'echelon': 3 if echelle and echelle <= 11 else None,
                    'contract_type': 'titulaire',
                    'hire_date': date(2015, 1, 10),
                    'status': 'active',
                }
            )
            if was_created:
                created += 1
                self.stdout.write(f'  ✓ Created employee: {emp.full_name} ({email})')
            else:
                self.stdout.write(f'  - Updated employee: {emp.full_name} ({email})')
                
            # Auto-provision user
            if not emp.user:
                # Username: employee full name without spaces (lowercased). Ensure uniqueness.
                base_username = ''.join(emp.full_name.split()).lower()
                username = base_username
                i = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{i}"
                    i += 1
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first,
                    last_name=last,
                    password='rabat2025'
                )
                # Auto-assign Normal User role
                try:
                    normal_user_group = Group.objects.get(name='Normal User')
                    user.groups.add(normal_user_group)
                except Group.DoesNotExist:
                    self.stdout.write(self.style.WARNING('  Normal User role not found. Run seed_roles first.'))
                
                emp.user = user
                emp.save()
                self.stdout.write(f'    Created user: {username} (password: rabat2025) with Normal User role')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Seeded {created} new employees (others updated). Default password: rabat2025'))
