from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from apps.employees.models import Employee


class LeaveType(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    paid = models.BooleanField(default=True)
    annual_days = models.DecimalField(max_digits=5, decimal_places=2, default=22)  # default normal leave 22 days/year
    prorata_monthly = models.BooleanField(default=True)
    carry_over_years = models.PositiveIntegerField(default=2)
    exclude_weekends = models.BooleanField(default=True)
    requires_approval = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class EmployeeLeaveBalance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)  # Changed from PROTECT to CASCADE to allow deletion
    year = models.PositiveIntegerField()
    opening = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    accrued = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    used = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    carried_over = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    expired = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    closing = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        unique_together = [('employee', 'leave_type', 'year')]
        ordering = ['-year']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} ({self.year})"

    def calculate_monthly_accrual(self, months_worked=None):
        """
        Calculate accrued leave based on months worked.
        Default: 1.5 days per month = 18 days per year (12 months)
        For 22 days/year: 1.83 days per month
        """
        from decimal import Decimal
        
        if not self.leave_type.prorata_monthly:
            # If not prorata, give full annual entitlement
            return Decimal(str(self.leave_type.annual_days))
        
        if months_worked is None:
            # Calculate months worked in the year based on employee hire date
            from datetime import date
            year_start = date(self.year, 1, 1)
            year_end = date(self.year, 12, 31)
            hire_date = self.employee.hire_date or year_start
            
            # If hired before year started, count full year
            if hire_date <= year_start:
                months_worked = 12
            # If hired after year ended, no accrual
            elif hire_date > year_end:
                months_worked = 0
            else:
                # Count months from hire date to end of year
                months_worked = 12 - hire_date.month + 1
        
        # Calculate monthly rate: annual_days / 12
        monthly_rate = Decimal(str(self.leave_type.annual_days)) / Decimal('12')
        accrued = monthly_rate * Decimal(str(months_worked))
        
        return accrued.quantize(Decimal('0.01'))

    def recalculate_balance(self):
        """
        Recalculate the closing balance.
        Formula: closing = opening + accrued + carried_over - used - expired
        """
        from decimal import Decimal
        self.closing = (
            Decimal(str(self.opening or 0)) +
            Decimal(str(self.accrued or 0)) +
            Decimal(str(self.carried_over or 0)) -
            Decimal(str(self.used or 0)) -
            Decimal(str(self.expired or 0))
        )
        return self.closing

    def deduct_leave(self, days):
        """
        Deduct approved leave days from the balance.
        Updates 'used' and recalculates closing balance.
        """
        from decimal import Decimal
        self.used = (self.used or 0) + Decimal(str(days))
        self.recalculate_balance()
        self.save()

    def calculate_expiration(self, current_year):
        """
        Calculate how many days should expire based on carry_over_years setting.
        Only applies to old balances that exceeded the carry-over period.
        """
        years_old = current_year - self.year
        if years_old > self.leave_type.carry_over_years:
            # All remaining balance expires
            return self.closing
        return 0


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)  # Changed from PROTECT to CASCADE
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.leave_type} {self.start_date}→{self.end_date} ({self.status})"

    def compute_days(self):
        # Basic working-days calc excluding weekends; holidays not considered yet
        from datetime import timedelta
        total = 0
        d = self.start_date
        while d <= self.end_date:
            if self.leave_type.exclude_weekends:
                if d.weekday() < 5:  # Mon-Fri
                    total += 1
            else:
                total += 1
            d += timedelta(days=1)
        self.days = total
        return self.days

    def deduct_from_balance(self):
        """
        Automatically deduct approved leave from employee's balance.
        Finds the balance for the leave request's year and leave type.
        """
        if self.status == 'approved' and self.days > 0:
            year = self.start_date.year
            balance, created = EmployeeLeaveBalance.objects.get_or_create(
                employee=self.employee,
                leave_type=self.leave_type,
                year=year,
                defaults={
                    'opening': 0,
                    'accrued': self.leave_type.annual_days,
                    'used': 0,
                    'carried_over': 0,
                    'expired': 0,
                    'closing': self.leave_type.annual_days,
                }
            )
            balance.deduct_leave(self.days)


class LeaveRequestHistory(models.Model):
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='history')
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Leave Request Histories'

    def __str__(self):
        return f"{self.leave_request.employee} - {self.previous_status} → {self.new_status} by {self.action_by} at {self.timestamp}"
