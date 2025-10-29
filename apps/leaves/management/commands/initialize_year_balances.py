from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from apps.employees.models import Employee
from apps.leaves.models import LeaveType, EmployeeLeaveBalance
from decimal import Decimal


class Command(BaseCommand):
    help = "Initialize new year leave balances for all employees on January 1st"

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=timezone.now().year,
            help='Year for which to initialize balances (default: current year)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force initialization even if balances already exist'
        )

    def handle(self, *args, **options):
        target_year = options['year']
        force = options['force']

        self.stdout.write(self.style.SUCCESS(f'\n🎉 Initializing leave balances for year {target_year}...\n'))

        # Get all active employees
        employees = Employee.objects.all()
        if not employees.exists():
            self.stdout.write(self.style.WARNING('No employees found.'))
            return

        # Get all active leave types
        leave_types = LeaveType.objects.filter(is_active=True)
        if not leave_types.exists():
            self.stdout.write(self.style.WARNING('No active leave types found.'))
            return

        previous_year = target_year - 1
        created_count = 0
        updated_count = 0
        skipped_count = 0
        total_carried_over = Decimal('0')
        total_expired = Decimal('0')

        for employee in employees:
            self.stdout.write(f'\n👤 {employee.full_name} (ID: {employee.employee_id})')
            
            for leave_type in leave_types:
                # Check for previous year balance
                try:
                    previous_balance = EmployeeLeaveBalance.objects.get(
                        employee=employee,
                        leave_type=leave_type,
                        year=previous_year
                    )
                except EmployeeLeaveBalance.DoesNotExist:
                    previous_balance = None

                # Calculate carry-over and expiration
                carry_over_amount = Decimal('0')
                expired_amount = Decimal('0')
                
                if previous_balance and previous_balance.closing > 0:
                    # Check if balance has expired
                    years_old = target_year - previous_balance.year
                    if years_old > leave_type.carry_over_years:
                        # Balance expired
                        expired_amount = previous_balance.closing
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⚠️  {leave_type.name}: {expired_amount} days expired'
                            )
                        )
                    else:
                        # Carry over remaining balance
                        carry_over_amount = previous_balance.closing
                        self.stdout.write(
                            f'  ✓ {leave_type.name}: {carry_over_amount} days carried over'
                        )
                
                # Calculate accrued for new year
                # For January 1st initialization, calculate full year prorata based on hire date
                new_balance_obj = EmployeeLeaveBalance(
                    employee=employee,
                    leave_type=leave_type,
                    year=target_year,
                    opening=carry_over_amount,
                    accrued=Decimal('0'),  # Will calculate below
                    used=Decimal('0'),
                    carried_over=carry_over_amount,
                    expired=Decimal('0'),
                    closing=Decimal('0')
                )
                
                # Calculate prorata accrual
                accrued_days = new_balance_obj.calculate_monthly_accrual()
                new_balance_obj.accrued = accrued_days
                new_balance_obj.recalculate_balance()

                # Check if balance already exists for target year
                existing_balance = EmployeeLeaveBalance.objects.filter(
                    employee=employee,
                    leave_type=leave_type,
                    year=target_year
                ).first()

                if existing_balance:
                    if force:
                        # Update existing balance
                        existing_balance.opening = carry_over_amount
                        existing_balance.carried_over = carry_over_amount
                        existing_balance.accrued = accrued_days
                        existing_balance.recalculate_balance()
                        existing_balance.save()
                        updated_count += 1
                        self.stdout.write(
                            f'  ↻ {leave_type.name}: Updated (Opening: {carry_over_amount}, Accrued: {accrued_days}, Closing: {existing_balance.closing})'
                        )
                    else:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'  - {leave_type.name}: Already exists (use --force to overwrite)'
                            )
                        )
                else:
                    # Create new balance
                    new_balance_obj.save()
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {leave_type.name}: Created (Opening: {carry_over_amount}, Accrued: {accrued_days}, Closing: {new_balance_obj.closing})'
                        )
                    )

                # Update previous balance to mark expired days if needed
                if previous_balance and expired_amount > 0:
                    previous_balance.expired = expired_amount
                    previous_balance.recalculate_balance()
                    previous_balance.save()
                
                total_carried_over += carry_over_amount
                total_expired += expired_amount

        # Print summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(f'\n📊 New Year Balance Initialization Summary:'))
        self.stdout.write(f'  • Target Year: {target_year}')
        self.stdout.write(f'  • Employees Processed: {employees.count()}')
        self.stdout.write(f'  • Leave Types: {leave_types.count()}')
        self.stdout.write(f'  • New Balances Created: {created_count}')
        if force:
            self.stdout.write(f'  • Existing Balances Updated: {updated_count}')
        self.stdout.write(f'  • Balances Skipped (already exist): {skipped_count}')
        self.stdout.write(f'  • Total Days Carried Over: {total_carried_over}')
        self.stdout.write(f'  • Total Days Expired: {total_expired}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Balance initialization complete for {target_year}!'))
        self.stdout.write(f'\n💡 Tip: Run this command automatically on January 1st each year.')
        self.stdout.write(f'   Or schedule it with: python manage.py initialize_year_balances\n')
