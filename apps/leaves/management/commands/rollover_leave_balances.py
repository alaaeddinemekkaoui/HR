from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from apps.employees.models import Employee
from apps.leaves.models import LeaveType, EmployeeLeaveBalance
from decimal import Decimal


class Command(BaseCommand):
    help = "Rollover leave balances to the next year, calculating carry-overs and expirations"

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-year',
            type=int,
            default=timezone.now().year - 1,
            help='Year to roll over from (default: last year)'
        )
        parser.add_argument(
            '--to-year',
            type=int,
            default=timezone.now().year,
            help='Year to roll over to (default: current year)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would happen without making changes'
        )

    def handle(self, *args, **options):
        from_year = options['from_year']
        to_year = options['to_year']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING(f'🔍 DRY RUN MODE - No changes will be saved'))
        
        self.stdout.write(f'\n📅 Rolling over leave balances from {from_year} to {to_year}...\n')

        # Get all employees
        employees = Employee.objects.all()
        if not employees.exists():
            self.stdout.write(self.style.WARNING('No employees found.'))
            return

        # Get all active leave types
        leave_types = LeaveType.objects.filter(is_active=True)
        if not leave_types.exists():
            self.stdout.write(self.style.WARNING('No active leave types found.'))
            return

        created_count = 0
        carried_over_total = Decimal('0')
        expired_total = Decimal('0')

        for employee in employees:
            self.stdout.write(f'\n👤 Processing {employee.full_name}...')
            
            for leave_type in leave_types:
                # Get balance from previous year
                try:
                    old_balance = EmployeeLeaveBalance.objects.get(
                        employee=employee,
                        leave_type=leave_type,
                        year=from_year
                    )
                except EmployeeLeaveBalance.DoesNotExist:
                    # No balance from previous year, create new one with zero carry-over
                    old_balance = None

                # Calculate carry-over and expiration
                carry_over_amount = Decimal('0')
                expired_amount = Decimal('0')
                
                if old_balance:
                    # Check if balance has expired based on carry_over_years
                    years_old = to_year - old_balance.year
                    if years_old > leave_type.carry_over_years:
                        # All remaining balance expires
                        expired_amount = old_balance.closing
                        self.stdout.write(
                            self.style.WARNING(
                                f'  ⚠️  {leave_type.name}: {expired_amount} days expired (older than {leave_type.carry_over_years} years)'
                            )
                        )
                    else:
                        # Carry over the closing balance
                        carry_over_amount = old_balance.closing if old_balance.closing > 0 else Decimal('0')
                        if carry_over_amount > 0:
                            self.stdout.write(
                                f'  ✓ {leave_type.name}: {carry_over_amount} days carried over'
                            )

                # Calculate monthly accrual for the new year
                # Assuming full year if employee already exists
                accrued_amount = leave_type.annual_days

                # Calculate opening and closing for new year
                opening_amount = carry_over_amount
                closing_amount = opening_amount + accrued_amount

                if not dry_run:
                    # Create or update balance for new year
                    new_balance, created = EmployeeLeaveBalance.objects.get_or_create(
                        employee=employee,
                        leave_type=leave_type,
                        year=to_year,
                        defaults={
                            'opening': opening_amount,
                            'accrued': accrued_amount,
                            'used': Decimal('0'),
                            'carried_over': carry_over_amount,
                            'expired': Decimal('0'),
                            'closing': closing_amount,
                        }
                    )
                    
                    if not created:
                        # Update existing balance
                        new_balance.carried_over = carry_over_amount
                        new_balance.opening = opening_amount
                        new_balance.recalculate_balance()
                        new_balance.save()

                    # Update old balance to mark expired days
                    if old_balance and expired_amount > 0:
                        old_balance.expired = expired_amount
                        old_balance.recalculate_balance()
                        old_balance.save()
                    
                    if created:
                        created_count += 1
                
                carried_over_total += carry_over_amount
                expired_total += expired_amount

        summary_style = self.style.SUCCESS if not dry_run else self.style.WARNING
        self.stdout.write('\n' + '='*60)
        self.stdout.write(summary_style(f'\n📊 Summary:'))
        self.stdout.write(f'  • Employees processed: {employees.count()}')
        self.stdout.write(f'  • Leave types processed: {leave_types.count()}')
        if not dry_run:
            self.stdout.write(f'  • New balances created: {created_count}')
        self.stdout.write(f'  • Total days carried over: {carried_over_total}')
        self.stdout.write(f'  • Total days expired: {expired_total}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n⚠️  This was a DRY RUN. Run without --dry-run to apply changes.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Leave balance rollover completed!'))
