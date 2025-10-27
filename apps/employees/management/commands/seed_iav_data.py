from django.core.management.base import BaseCommand
from apps.employees.models import Direction, Division, Service, Departement, Filiere, Grade, Position


class Command(BaseCommand):
    help = 'Seed IAV Hassan II organizational structure with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding Grades (Moroccan Public Sector)...')
        grades_data = [
            # Échelle 11 - Hors Échelle (Cadres Supérieurs)
            {'name': 'Ingénieur en Chef', 'code': 'ING_CHEF', 'category': 'cadre_superieur'},
            {'name': 'Architecte en Chef', 'code': 'ARCH_CHEF', 'category': 'cadre_superieur'},
            {'name': 'Médecin Spécialiste en Chef', 'code': 'MED_CHEF', 'category': 'cadre_superieur'},
            
            # Échelle 11 (Cadres Supérieurs)
            {'name': 'Ingénieur Principal', 'code': 'ING_PRIN', 'category': 'cadre_superieur'},
            {'name': 'Architecte Principal', 'code': 'ARCH_PRIN', 'category': 'cadre_superieur'},
            {'name': 'Administrateur Principal', 'code': 'ADM_PRIN', 'category': 'cadre_superieur'},
            
            # Échelle 10 (Cadres)
            {'name': 'Ingénieur d\'État 1er Grade', 'code': 'ING_1G', 'category': 'cadre'},
            {'name': 'Architecte 1er Grade', 'code': 'ARCH_1G', 'category': 'cadre'},
            {'name': 'Médecin 1er Grade', 'code': 'MED_1G', 'category': 'cadre'},
            {'name': 'Administrateur 1er Grade', 'code': 'ADM_1G', 'category': 'cadre'},
            
            # Échelle 10 (Cadres)
            {'name': 'Ingénieur d\'État', 'code': 'ING', 'category': 'cadre'},
            {'name': 'Architecte', 'code': 'ARCH', 'category': 'cadre'},
            {'name': 'Administrateur', 'code': 'ADM', 'category': 'cadre'},
            {'name': 'Professeur Agrégé', 'code': 'PROF_AGREGE', 'category': 'cadre'},
            
            # Échelle 9 (Maîtrise)
            {'name': 'Technicien 1er Grade', 'code': 'TECH_1G', 'category': 'maitrise'},
            {'name': 'Contrôleur 1er Grade', 'code': 'CTRL_1G', 'category': 'maitrise'},
            {'name': 'Infirmier Principal', 'code': 'INF_PRIN', 'category': 'maitrise'},
            
            # Échelle 8 (Maîtrise)
            {'name': 'Technicien', 'code': 'TECH', 'category': 'maitrise'},
            {'name': 'Contrôleur', 'code': 'CTRL', 'category': 'maitrise'},
            {'name': 'Infirmier', 'code': 'INF', 'category': 'maitrise'},
            
            # Échelle 7 (Maîtrise)
            {'name': 'Adjoint Technique 1er Grade', 'code': 'ADJ_TECH_1G', 'category': 'maitrise'},
            {'name': 'Adjoint Administratif 1er Grade', 'code': 'ADJ_ADM_1G', 'category': 'maitrise'},
            
            # Échelle 6 (Maîtrise)
            {'name': 'Adjoint Technique', 'code': 'ADJ_TECH', 'category': 'maitrise'},
            {'name': 'Adjoint Administratif', 'code': 'ADJ_ADM', 'category': 'maitrise'},
            
            # Échelle 5-4 (Exécution)
            {'name': 'Agent d\'Accueil', 'code': 'AG_ACC', 'category': 'execution'},
            {'name': 'Agent Administratif', 'code': 'AG_ADM', 'category': 'execution'},
            {'name': 'Gardien', 'code': 'GARD', 'category': 'execution'},
            {'name': 'Chauffeur', 'code': 'CHAUF', 'category': 'execution'},
        ]
        
        for grade_data in grades_data:
            try:
                grade, created = Grade.objects.get_or_create(
                    code=grade_data['code'],
                    defaults=grade_data
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created grade: {grade.name}'))
                else:
                    # Update if exists
                    for key, value in grade_data.items():
                        setattr(grade, key, value)
                    grade.save()
                    self.stdout.write(f'  - Updated grade: {grade.name}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ! Grade {grade_data["code"]} exists: {str(e)}'))
        
        self.stdout.write('Seeding Positions...')
        positions_data = [
            {'name': 'Directeur', 'code': 'DIR', 'position_type': 'directeur'},
            {'name': 'Chef de Direction', 'code': 'CHEF_DIR', 'position_type': 'chef_direction'},
            {'name': 'Chef Adjoint', 'code': 'CHEF_ADJ', 'position_type': 'chef_adjoint'},
            {'name': 'Chef de Division', 'code': 'CHEF_DIV', 'position_type': 'chef_division'},
            {'name': 'Chef de Service', 'code': 'CHEF_SRV', 'position_type': 'chef_service'},
            {'name': 'Chef de Département', 'code': 'CHEF_DEPT', 'position_type': 'chef_departement'},
            {'name': 'Chef de Filière', 'code': 'CHEF_FIL', 'position_type': 'chef_filiere'},
            {'name': 'Inspecteur', 'code': 'INSP', 'position_type': 'inspecteur'},
            {'name': 'Ingénieur', 'code': 'ING', 'position_type': 'employee'},
            {'name': 'Professeur', 'code': 'PROF', 'position_type': 'employee'},
            {'name': 'Technicien', 'code': 'TECH', 'position_type': 'employee'},
            {'name': 'Secrétaire', 'code': 'SEC', 'position_type': 'employee'},
            {'name': 'Agent Administratif', 'code': 'AG_ADM', 'position_type': 'employee'},
        ]
        
        for pos_data in positions_data:
            try:
                position, created = Position.objects.get_or_create(
                    code=pos_data['code'],
                    defaults=pos_data
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created position: {position.name}'))
                else:
                    # Update if exists
                    for key, value in pos_data.items():
                        setattr(position, key, value)
                    position.save()
                    self.stdout.write(f'  - Updated position: {position.name}')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ! Position {pos_data["code"]} error: {str(e)}'))
        
        self.stdout.write('Seeding Directions...')
        directions_data = [
            {'name': 'Direction Générale', 'code': 'DG'},
            {'name': 'Secrétariat Général', 'code': 'SG'},
            {'name': 'Direction des Études', 'code': 'DE'},
        ]
        
        for dir_data in directions_data:
            direction, created = Direction.objects.get_or_create(
                code=dir_data['code'],
                defaults=dir_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created direction: {direction.name}'))
        
        self.stdout.write('Seeding Divisions and Services...')
        
        # Secrétariat Général - IT Service
        sg = Direction.objects.get(code='SG')
        Service.objects.get_or_create(
            direction=sg,
            code='IT',
            defaults={'name': 'Service Informatique'}
        )

        # Direction des Études - Divisions and Services
        de = Direction.objects.get(code='DE')
        
        div_scol, _ = Division.objects.get_or_create(
            direction=de,
            code='SCOL',
            defaults={'name': 'Division Scolarité'}
        )
        
        Service.objects.get_or_create(
            division=div_scol,
            code='INSCR',
            defaults={'name': 'Service Inscriptions'}
        )
        
        # Départements for Direction des Études only
        self.stdout.write('Seeding Départements for Direction des Études...')
        
        dept_info, _ = Departement.objects.get_or_create(
            direction=de,
            code='INFO',
            defaults={
                'name': 'Département Informatique',
                'description': 'Département des sciences informatiques'
            }
        )
        
        dept_genie, _ = Departement.objects.get_or_create(
            direction=de,
            code='GENIE',
            defaults={
                'name': 'Département Génie Civil',
                'description': 'Département de génie civil et construction'
            }
        )
        
        dept_agro, _ = Departement.objects.get_or_create(
            direction=de,
            code='AGRO',
            defaults={
                'name': 'Département Agronomie',
                'description': 'Département des sciences agronomiques'
            }
        )
        
        # Filières under Départements
        self.stdout.write('Seeding Filières...')
        
        # Département Informatique
        Filiere.objects.get_or_create(
            departement=dept_info,
            code='GL',
            defaults={
                'name': 'Filière Génie Logiciel',
                'description': 'Formation en développement de logiciels'
            }
        )
        
        Filiere.objects.get_or_create(
            departement=dept_info,
            code='IA',
            defaults={
                'name': 'Filière Intelligence Artificielle',
                'description': 'Formation en IA et data science'
            }
        )
        
        Filiere.objects.get_or_create(
            departement=dept_info,
            code='CYBER',
            defaults={
                'name': 'Filière Cybersécurité',
                'description': 'Formation en sécurité informatique'
            }
        )
        
        # Département Génie Civil
        Filiere.objects.get_or_create(
            departement=dept_genie,
            code='BTP',
            defaults={
                'name': 'Filière Bâtiment et Travaux Publics',
                'description': 'Formation en construction et infrastructure'
            }
        )
        
        Filiere.objects.get_or_create(
            departement=dept_genie,
            code='STRUCT',
            defaults={
                'name': 'Filière Structures',
                'description': 'Formation en calcul et conception de structures'
            }
        )
        
        # Département Agronomie
        Filiere.objects.get_or_create(
            departement=dept_agro,
            code='PA',
            defaults={
                'name': 'Filière Production Agricole',
                'description': 'Formation en production végétale et animale'
            }
        )
        
        Filiere.objects.get_or_create(
            departement=dept_agro,
            code='IAA',
            defaults={
                'name': 'Filière Industries Agroalimentaires',
                'description': 'Formation en transformation alimentaire'
            }
        )
        
        # Secrétariat Général - Division Administrative
        div_adm, _ = Division.objects.get_or_create(
            direction=sg,
            code='ADM',
            defaults={'name': 'Division Administrative'}
        )
        Service.objects.get_or_create(
            division=div_adm,
            code='COUR',
            defaults={'name': 'Service Courrier'}
        )
        
        self.stdout.write(self.style.SUCCESS('\n✓ Seeding completed successfully!'))
        self.stdout.write(self.style.WARNING('\nNext steps:'))
        self.stdout.write('  1. Run migrations: docker compose exec web python manage.py migrate')
        self.stdout.write('  2. Access Django admin to manage organizational structure')
