from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.management import call_command
from django.contrib.auth import get_user_model
from apps.employees.models import Employee
from apps.leaves.models import LeaveRequest

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
