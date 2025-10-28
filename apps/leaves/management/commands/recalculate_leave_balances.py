from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.employees.models import Employee
from apps.leaves.models import EmployeeLeaveBalance


class Command(BaseCommand):
    help = "Recalculate all employee leave balances based on monthly accrual and usage"

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Year for which to recalculate balances (default: current year)'
        )
        parser.add_argument(
            '--employee-id',
            type=str,
            help='Recalculate for a specific employee only (employee_id)'
        )

    def handle(self, *args, **options):
        year = options['year']
        employee_id = options.get('employee_id')

        self.stdout.write(f'\n🔄 Recalculating leave balances for year {year}...\n')

        # Filter employees
        if employee_id:
            employees = Employee.objects.filter(employee_id=employee_id)
            if not employees.exists():
                self.stdout.write(self.style.ERROR(f'Employee with ID {employee_id} not found.'))
                return
        else:
            employees = Employee.objects.all()

        if not employees.exists():
            self.stdout.write(self.style.WARNING('No employees found.'))
            return

        updated_count = 0

        for employee in employees:
            self.stdout.write(f'\n👤 {employee.full_name} (ID: {employee.employee_id})')
            
            # Get all balances for this employee in the specified year
            balances = EmployeeLeaveBalance.objects.filter(
                employee=employee,
                year=year
            ).select_related('leave_type')

            if not balances.exists():
                self.stdout.write(self.style.WARNING(f'  No balances found for {year}'))
                continue

            for balance in balances:
                old_accrued = balance.accrued
                old_closing = balance.closing

                # Recalculate monthly accrual
                balance.accrued = balance.calculate_monthly_accrual()
                
                # Recalculate closing balance
                balance.recalculate_balance()
                balance.save()

                if old_accrued != balance.accrued or old_closing != balance.closing:
                    self.stdout.write(
                        f'  ✓ {balance.leave_type.name}: '
                        f'Accrued {old_accrued} → {balance.accrued}, '
                        f'Closing {old_closing} → {balance.closing}'
                    )
                    updated_count += 1
                else:
                    self.stdout.write(
                        f'  - {balance.leave_type.name}: No changes (Closing: {balance.closing})'
                    )

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\n✅ Recalculation complete!'))
        self.stdout.write(f'  • Employees processed: {employees.count()}')
        self.stdout.write(f'  • Balances updated: {updated_count}')
