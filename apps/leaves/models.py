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
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
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


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
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
