from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
import random
from apps.employees.models import Direction, Division, Service, Grade, Position, Employee

class Command(BaseCommand):
    help = 'Seed a set of sample employees and auto-provision user accounts (password: rabat2025)'

    def handle(self, *args, **options):
        # Ensure org and taxonomy exist
        if Direction.objects.count() == 0 or Grade.objects.count() == 0 or Position.objects.count() == 0:
            self.stdout.write(self.style.WARNING('Org/Grades/Positions not found. Run seed_org_basics first. Running now...'))
            from django.core.management import call_command
            call_command('seed_org_basics')

        dg = Direction.objects.get(code='DG')
        de = Direction.objects.get(code='DE')
        drh = Division.objects.get(direction=dg, code='DRH')
        sgp = Service.objects.get(code='SGP')
        scol = Service.objects.get(code='SCOL')

        grades = {g.code: g for g in Grade.objects.all()}
        positions = {p.code: p for p in Position.objects.all()}

        today = timezone.now().date()
        samples = [
            # first_name, last_name, email, cin, direction, division, service, position, grade, echelle
            ('Ahmed', 'El Mansouri', 'ahmed.mansouri@example.com', 'CIN10001', dg, drh, sgp, positions['CS'], grades['ING'], 10),
            ('Fatima', 'Zahra', 'fatima.zahra@example.com', 'CIN10002', de, None, scol, positions['ING-POS'], grades['ING'], 9),
            ('Youssef', 'Bennani', 'youssef.bennani@example.com', 'CIN10003', dg, drh, sgp, positions['TECH-POS'], grades['TECH'], 7),
            ('Salma', 'Haddad', 'salma.haddad@example.com', 'CIN10004', de, None, None, positions['SEC-POS'], grades['SEC'], 5),
            ('Hassan', 'Amrani', 'hassan.amrani@example.com', 'CIN10005', dg, None, None, positions['CDIR'], grades['ING-P'], None),
        ]

        created = 0
        for first, last, email, cin, direction, division, service, position, grade, echelle in samples:
            emp, was_created = Employee.objects.update_or_create(
                email=email,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'cin': cin,
                    'phone': '0612345678',
                    'date_of_birth': date(1985, 5, 15),
                    'address': 'Rabat, Morocco',
                    'ppr': None,
                    'direction': direction,
                    'division': division,
                    'service': service,
                    'position': position,
                    'grade': grade,
                    'echelle': echelle,
                    'echelon': 3 if echelle else None,
                    'hors_echelle': False if echelle else True,
                    'contract_type': 'titulaire',
                    'hire_date': date(2012, 1, 10),
                    'contract_start_date': None,
                    'contract_end_date': None,
                    'titularisation_date': date(2013, 1, 10),
                    'status': 'active',
                }
            )
            if was_created:
                created += 1
            # Auto-provision user
            if not emp.user:
                user, _ = User.objects.get_or_create(username=email, defaults={'email': email, 'first_name': first, 'last_name': last})
                user.set_password('rabat2025')
                user.save()
                emp.user = user
                emp.save()
        
        self.stdout.write(self.style.SUCCESS(f'✅ Seeded {created} employees (others updated). Default password: rabat2025'))
