from django.core.management.base import BaseCommand
from apps.employees.models import Grade, GradeProgressionRule

class Command(BaseCommand):
    help = 'Seed common grade progression rules (with/without exam)'

    def handle(self, *args, **options):
        if Grade.objects.count() == 0:
            self.stdout.write(self.style.WARNING('No grades found. Run seed_org_basics first.'))
            return

        def add_rule(src_code, tgt_code, with_exam, without_exam, desc):
            try:
                src = Grade.objects.get(code=src_code)
                tgt = Grade.objects.get(code=tgt_code)
            except Grade.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Skip rule {src_code}->{tgt_code}: grade missing'))
                return
            GradeProgressionRule.objects.update_or_create(
                source_grade=src, target_grade=tgt,
                defaults={
                    'years_with_exam': with_exam,
                    'years_without_exam': without_exam,
                    'description': desc,
                    'is_active': True,
                }
            )
            self.stdout.write(f'  ✔ {src.code} → {tgt.code} ({with_exam}y exam / {without_exam}y no-exam)')

        self.stdout.write('Seeding grade rules...')
        add_rule('ING', 'ING-P', 3, 5, 'Promotion Ingénieur vers Ingénieur Principal')
        # Add a couple of technician advancements if exist
        add_rule('TECH', 'ING', None, 6, 'Technicien vers Ingénieur (sans concours)')

        self.stdout.write(self.style.SUCCESS('✅ Grade rules seeded'))
