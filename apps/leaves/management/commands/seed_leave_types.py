"""
Management command to seed Moroccan public sector leave types with official rules.
"""
from django.core.management.base import BaseCommand
from apps.leaves.models import LeaveType


class Command(BaseCommand):
    help = 'Seed Moroccan public sector leave types with official quotas and rules'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🇲🇦 Seeding Moroccan Leave Types...\n'))
        
        leave_types_data = [
            {
                'name': 'Congé Annuel',
                'code': 'CA',
                'description': 'Annual paid leave - 22 working days per year',
                'annual_days': 22,
                'prorata_monthly': True,
                'exclude_weekends': True,
                'carry_over_years': 2,
                'paid': True,
                'requires_approval': True,
            },
            {
                'name': 'Congé de Maladie',
                'code': 'CM',
                'description': 'Sick leave - requires medical certificate after 3 days',
                'annual_days': 180,  # Up to 6 months per year
                'prorata_monthly': False,
                'exclude_weekends': True,
                'carry_over_years': 0,  # Cannot carry over
                'paid': True,
                'requires_approval': True,
            },
            {
                'name': 'Congé de Maternité',
                'code': 'CMAT',
                'description': 'Maternity leave - 14 weeks (98 days)',
                'annual_days': 98,
                'prorata_monthly': False,
                'exclude_weekends': False,  # Counts all calendar days
                'carry_over_years': 0,
                'paid': True,
                'requires_approval': True,
            },
            {
                'name': 'Congé de Paternité',
                'code': 'CPAT',
                'description': 'Paternity leave - 3 days',
                'annual_days': 3,
                'prorata_monthly': False,
                'exclude_weekends': True,
                'carry_over_years': 0,
                'paid': True,
                'requires_approval': True,
            },
            {
                'name': 'Congé Exceptionnel - Mariage',
                'code': 'CE-MAR',
                'description': 'Exceptional leave for marriage - 4 days',
                'annual_days': 4,
                'prorata_monthly': False,
                'exclude_weekends': True,
                'carry_over_years': 0,
                'paid': True,
                'requires_approval': True,
            },
            {
                'name': 'Congé Exceptionnel - Décès Conjoint/Parents/Enfants',
                'code': 'CE-DEC1',
                'description': 'Exceptional leave for death of spouse/parents/children - 3 days',
                'annual_days': 3,
                'prorata_monthly': False,
                'exclude_weekends': True,
                'carry_over_years': 0,
                'paid': True,
                'requires_approval': True,
            },
            {
                'name': 'Congé Exceptionnel - Décès Beaux-parents/Frères/Sœurs',
                'code': 'CE-DEC2',
                'description': 'Exceptional leave for death of in-laws/siblings - 2 days',
                'annual_days': 2,
                'prorata_monthly': False,
                'exclude_weekends': True,
                'carry_over_years': 0,
                'paid': True,
                'requires_approval': True,
            },
            {
                'name': 'Congé Exceptionnel - Naissance',
                'code': 'CE-NAIS',
                'description': 'Exceptional leave for childbirth - 2 days',
                'annual_days': 2,
                'prorata_monthly': False,
                'exclude_weekends': True,
                'carry_over_years': 0,
                'paid': True,
                'requires_approval': True,
            },
            {
                'name': 'Congé Exceptionnel - Circoncision',
                'code': 'CE-CIRC',
                'description': 'Exceptional leave for circumcision - 2 days',
                'annual_days': 2,
                'prorata_monthly': False,
                'exclude_weekends': True,
                'carry_over_years': 0,
                'paid': True,
                'requires_approval': True,
            },
            {
                'name': 'Congé sans Solde',
                'code': 'CSS',
                'description': 'Unpaid leave - granted upon request, no fixed quota',
                'annual_days': 0,  # No fixed quota
                'prorata_monthly': False,
                'exclude_weekends': True,
                'carry_over_years': 0,
                'paid': False,
                'requires_approval': True,
            },
            {
                'name': 'Congé Administratif',
                'code': 'CADM',
                'description': 'Administrative leave - granted by administration',
                'annual_days': 0,  # No fixed quota, granted as needed
                'prorata_monthly': False,
                'exclude_weekends': True,
                'carry_over_years': 0,
                'paid': True,
                'requires_approval': True,
            },
            {
                'name': 'Congé pour Pèlerinage',
                'code': 'CPEL',
                'description': 'Pilgrimage leave (Hajj) - once in career, 30 days',
                'annual_days': 30,
                'prorata_monthly': False,
                'exclude_weekends': False,  # Counts all calendar days
                'carry_over_years': 0,
                'paid': True,
                'requires_approval': True,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for data in leave_types_data:
            leave_type, created = LeaveType.objects.update_or_create(
                code=data['code'],
                defaults=data
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created: {leave_type.name} ({leave_type.code})'))
                created_count += 1
            else:
                self.stdout.write(f'  ♻️  Updated: {leave_type.name} ({leave_type.code})')
                updated_count += 1
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'🎉 Leave types seeded successfully!'))
        self.stdout.write(f'   Created: {created_count}')
        self.stdout.write(f'   Updated: {updated_count}')
        self.stdout.write('='*60)
