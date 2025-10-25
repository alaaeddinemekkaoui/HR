from django.core.management.base import BaseCommand
from apps.employees.models import Direction, Division, Service, Grade, Position

class Command(BaseCommand):
    help = 'Seed basic organization (Directions/Divisions/Services), Grades and Positions'

    def handle(self, *args, **options):
        self.stdout.write('Seeding organization basics...')

        # Directions
        dirs = [
            ('Direction Générale', 'DG', 'Direction Générale'),
            ('Direction des Études', 'DE', 'Direction des Études'),
            ('Direction Administrative', 'DA', 'Direction Administrative'),
        ]
        for name, code, desc in dirs:
            Direction.objects.update_or_create(code=code, defaults={'name': name, 'description': desc, 'is_active': True})
        dg = Direction.objects.get(code='DG')
        de = Direction.objects.get(code='DE')

        # Divisions
        divisions = [
            (dg, 'DRH', 'Division des Ressources Humaines'),
            (de, 'D1', 'Division Pédagogie'),
        ]
        for direction, code, name in divisions:
            Division.objects.update_or_create(direction=direction, code=code, defaults={'name': name, 'is_active': True})
        drh = Division.objects.get(direction=dg, code='DRH')

        # Services (some under Division, some directly under Direction)
        services = [
            (None, drh, 'SGP', 'Service Gestion du Personnel'),
            (de, None, 'SCOL', 'Service Scolarité'),
        ]
        for direction, division, code, name in services:
            Service.objects.update_or_create(direction=direction, division=division, code=code, defaults={'name': name, 'is_active': True})

        # Grades - Complete IAV Hassan II structure (excluding medical/doctor grades, including teachers)
        grades = [
            # Administrative & Technical Staff
            ('Technicien 1ère classe', 'TECH1', 'maitrise'),
            ('Technicien 2ème classe', 'TECH2', 'maitrise'),
            ('Technicien 3ème classe', 'TECH3', 'maitrise'),
            ('Technicien 4ème classe', 'TECH4', 'maitrise'),
            ('Ingénieur', 'ING', 'cadre'),
            ('Ingénieur en Chef', 'ING-CHEF', 'cadre_superieur'),
            ('Ingénieur Principal', 'ING-P', 'cadre_superieur'),
            
            # Teaching Staff
            ('Professeur Assistant', 'PROF-ASST', 'cadre'),
            ('Professeur Habilité', 'PROF-HAB', 'cadre_superieur'),
            ('Professeur de l\'Enseignement Supérieur', 'PES', 'cadre_superieur'),
            
            # Support Staff
            ('Agent d\'Accueil', 'AG-ACC', 'execution'),
            ('Agent Administratif', 'AG-ADM', 'execution'),
            ('Secrétaire', 'SEC', 'execution'),
            ('Secrétaire de Direction', 'SEC-DIR', 'maitrise'),
            
            # Management
            ('Cadre Administratif', 'CAD-ADM', 'cadre'),
            ('Chef de Service', 'CHEF-SER', 'cadre_superieur'),
            ('Chef de Division', 'CHEF-DIV', 'cadre_superieur'),
        ]
        for name, code, category in grades:
            # Make idempotent across code or name uniqueness
            try:
                grade = Grade.objects.get(code=code)
                changed = False
                if grade.name != name:
                    grade.name = name
                    changed = True
                if grade.category != category:
                    grade.category = category
                    changed = True
                if not grade.is_active:
                    grade.is_active = True
                    changed = True
                if changed:
                    grade.save()
            except Grade.DoesNotExist:
                # Check by name to avoid unique name conflict
                try:
                    grade = Grade.objects.get(name=name)
                    grade.code = code
                    grade.category = category
                    grade.is_active = True
                    grade.save()
                except Grade.DoesNotExist:
                    Grade.objects.create(name=name, code=code, category=category, is_active=True)

        # Positions
        positions = [
            ('Chef de Direction', 'CDIR', 'chef_direction'),
            ('Chef de Division', 'CDIV', 'chef_division'),
            ('Chef de Service', 'CS', 'chef_service'),
            ('Ingénieur', 'ING-POS', 'employee'),
            ('Technicien', 'TECH-POS', 'employee'),
            ('Secrétaire', 'SEC-POS', 'employee'),
        ]
        for name, code, position_type in positions:
            Position.objects.update_or_create(code=code, defaults={'name': name, 'position_type': position_type, 'is_active': True})

        self.stdout.write(self.style.SUCCESS('✅ Seeded organization basics, grades, and positions'))
