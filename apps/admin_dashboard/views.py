from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
from apps.employees.models import Employee
from apps.leaves.models import LeaveRequest, EmployeeLeaveBalance
from apps.leaves.utils import approvals_scope_q_for_user

User = get_user_model()


class ITAdminOnlyMixin(UserPassesTestMixin):
    def test_user_passes(self, user):
        return user.is_authenticated and (
            user.is_superuser or 
            user.groups.filter(name='IT Admin').exists() or 
            user.groups.filter(name='HR Admin').exists()
        )

    def test_func(self):
        return self.test_user_passes(self.request.user)


class DashboardView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        # Calculate statistics
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(status='active').count()
        pending_leaves = LeaveRequest.objects.filter(status='pending').count()
        total_users = User.objects.count()
        
        context = {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'pending_leaves': pending_leaves,
            'total_users': total_users,
        }
        return render(request, 'admin_dashboard/index.html', context)


class DashboardRouterView(LoginRequiredMixin, View):
    """Route users to the appropriate dashboard based on their role/groups."""
    def get(self, request):
        user = request.user
        # IT/Admin users go to existing admin dashboard
        if user.is_superuser or user.groups.filter(name__in=['IT Admin']).exists():
            return redirect('admin_dashboard:admin')
        # HR users (both HR Admin and HR) go to HR dashboard
        if user.groups.filter(name__in=['HR Admin', 'HR']).exists():
            return redirect('admin_dashboard:hr')
        # Everyone else -> user dashboard
        return redirect('admin_dashboard:user')


class HROnlyMixin(UserPassesTestMixin):
    def test_user_passes(self, user):
        return user.is_authenticated and (
            user.is_superuser or
            user.groups.filter(name__in=['HR Admin', 'HR']).exists()
        )

    def test_func(self):
        return self.test_user_passes(self.request.user)


class HRDashboardView(LoginRequiredMixin, HROnlyMixin, View):
    """Dashboard for HR users with employee and leave insights."""
    def get(self, request):
        # Basic stats relevant to HR
        today = timezone.now().date()
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(status='active').count()
        pending_leaves = LeaveRequest.objects.filter(status='pending').count()
        # Hires this month (by hire_date)
        hires_this_month = Employee.objects.filter(hire_date__year=today.year, hire_date__month=today.month).count()

        # Headcount by status (top 5)
        status_breakdown = (
            Employee.objects.values('status').annotate(c=Count('id')).order_by('-c')[:5]
        )

        context = {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'pending_leaves': pending_leaves,
            'hires_this_month': hires_this_month,
            'status_breakdown': status_breakdown,
        }
        return render(request, 'admin_dashboard/hr.html', context)


class UserDashboardView(LoginRequiredMixin, View):
    """Dashboard for normal users showing personal info and quick actions."""
    def get(self, request):
        user = request.user
        emp = getattr(user, 'employee_profile', None)

        # My recent leave requests
        my_leaves = LeaveRequest.objects.none()
        my_balances = []
        approvals_count = 0

        if emp:
            my_leaves = emp.leave_requests.all()[:5]
            # Current year's balances, if any
            year = timezone.now().year
            my_balances = list(EmployeeLeaveBalance.objects.filter(employee=emp, year=year).select_related('leave_type')[:5])

        # If user is a supervisor, show pending approvals count in their scope
        scope_q = approvals_scope_q_for_user(user)
        if scope_q != Q(pk__in=[]):
            approvals_count = LeaveRequest.objects.filter(scope_q, status='pending').count()

        context = {
            'employee': emp,
            'my_leaves': my_leaves,
            'my_balances': my_balances,
            'approvals_count': approvals_count,
        }
        return render(request, 'admin_dashboard/user.html', context)
