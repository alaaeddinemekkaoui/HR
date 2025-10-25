from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import UserRegistrationForm
from django.contrib.auth.models import User, Group


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        groups = list(user.groups.values_list('name', flat=True))
        employee = getattr(user, 'employee_profile', None)
        history = []
        next_grade = []
        if employee:
            history = list(employee.history.select_related('employee').all()[:10])
            next_grade = employee.next_grade_eligibility()
        return render(request, 'authentication/profile.html', {
            'user_obj': user,
            'groups': groups,
            'employee': employee,
            'history': history,
            'next_grade': next_grade,
        })


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('employees:list')
        form = UserRegistrationForm()
        return render(request, 'authentication/register.html', {'form': form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('employees:list')
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Your account has been created.')
            return redirect('employees:list')
        return render(request, 'authentication/register.html', {'form': form})


class ITAdminOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or self.request.user.groups.filter(name='IT Admin').exists()
        )


class UserListView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        users = User.objects.all().order_by('username')
        groups = Group.objects.all().order_by('name')
        return render(request, 'authentication/users.html', {
            'users': users,
            'groups': groups,
        })
