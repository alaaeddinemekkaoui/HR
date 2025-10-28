from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from apps.employees.models import Employee
from .models import LeaveType, EmployeeLeaveBalance


@receiver(post_save, sender=Employee)
def create_leave_balances_for_new_employee(sender, instance, created, **kwargs):
    """
    Automatically create leave balances for a new employee when they are created.
    Creates balances for all active leave types for the current year.
    Uses monthly prorata calculation if employee hired mid-year.
    """
    if created:
        current_year = timezone.now().year
        leave_types = LeaveType.objects.filter(is_active=True)
        
        for leave_type in leave_types:
            balance, balance_created = EmployeeLeaveBalance.objects.get_or_create(
                employee=instance,
                leave_type=leave_type,
                year=current_year,
                defaults={
                    'opening': 0,
                    'accrued': 0,  # Will be calculated below
                    'used': 0,
                    'carried_over': 0,
                    'expired': 0,
                    'closing': 0,  # Will be calculated below
                }
            )
            
            if balance_created:
                # Calculate accrued based on hire date and prorata settings
                balance.accrued = balance.calculate_monthly_accrual()
                balance.recalculate_balance()
                balance.save()


@receiver(post_save, sender=LeaveType)
def create_balances_for_new_leave_type(sender, instance, created, **kwargs):
    """
    Automatically create leave balances for all employees when a new leave type is created.
    Only creates for active leave types and the current year.
    """
    if created and instance.is_active:
        current_year = timezone.now().year
        employees = Employee.objects.all()
        
        for employee in employees:
            EmployeeLeaveBalance.objects.get_or_create(
                employee=employee,
                leave_type=instance,
                year=current_year,
                defaults={
                    'opening': 0,
                    'accrued': instance.annual_days,
                    'used': 0,
                    'carried_over': 0,
                    'expired': 0,
                    'closing': instance.annual_days,
                }
            )
