from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.employees.models import Employee
from apps.leaves.models import LeaveType, EmployeeLeaveBalance


class Command(BaseCommand):
    help = "Create leave balances for all employees"

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Year for which to create balances (default: current year)'
        )

    def handle(self, *args, **options):
        year = options['year']
        self.stdout.write(f'Creating leave balances for year {year}...')

        # Get all active leave types
        leave_types = LeaveType.objects.filter(is_active=True)
        if not leave_types.exists():
            self.stdout.write(self.style.ERROR('No active leave types found. Run seed_leave_types first.'))
            return

        # Get all employees
        employees = Employee.objects.all()
        if not employees.exists():
            self.stdout.write(self.style.WARNING('No employees found.'))
            return

        created_count = 0
        skipped_count = 0

        for employee in employees:
            for leave_type in leave_types:
                # Check if balance already exists
                balance, created = EmployeeLeaveBalance.objects.get_or_create(
                    employee=employee,
                    leave_type=leave_type,
                    year=year,
                    defaults={
                        'opening': 0,
                        'accrued': leave_type.annual_days,  # Default to annual days
                        'used': 0,
                        'carried_over': 0,
                        'expired': 0,
                        'closing': leave_type.annual_days,  # Opening + Accrued - Used
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created balance for {employee.full_name} - {leave_type.name} ({year})'
                        )
                    )
                else:
                    skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Created {created_count} leave balances, skipped {skipped_count} existing.'
            )
        )
