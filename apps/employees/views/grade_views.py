from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from ..models import Grade
from ..forms.grade_forms import GradeForm


class ITAdminOrHRMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_superuser or user.groups.filter(name__in=['IT Admin', 'HR']).exists())


class GradeListView(LoginRequiredMixin, ITAdminOrHRMixin, View):
    def get(self, request):
        grades = Grade.objects.all().order_by('category', 'name')
        return render(request, 'employees/grades/grades.html', {'grades': grades})


class GradeCreateView(LoginRequiredMixin, ITAdminOrHRMixin, View):
    def get(self, request):
        form = GradeForm()
        return render(request, 'employees/grades/grade_form.html', {'form': form, 'mode': 'create'})

    def post(self, request):
        form = GradeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grade created.')
            return redirect('employees:grade_list')
        return render(request, 'employees/grades/grade_form.html', {'form': form, 'mode': 'create'})


class GradeEditView(LoginRequiredMixin, ITAdminOrHRMixin, View):
    def get(self, request, pk):
        grade = get_object_or_404(Grade, pk=pk)
        form = GradeForm(instance=grade)
        return render(request, 'employees/grades/grade_form.html', {'form': form, 'mode': 'edit', 'obj': grade})

    def post(self, request, pk):
        grade = get_object_or_404(Grade, pk=pk)
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grade updated.')
            return redirect('employees:grade_list')
        return render(request, 'employees/grades/grade_form.html', {'form': form, 'mode': 'edit', 'obj': grade})


class GradeDeleteView(LoginRequiredMixin, ITAdminOrHRMixin, View):
    def post(self, request, pk):
        grade = get_object_or_404(Grade, pk=pk)
        # Potentially protect grades used by employees or rules
        if grade.employees.exists():
            messages.error(request, 'Cannot delete grade while employees are assigned to it.')
            return redirect('employees:grade_list')
        if grade.progression_from.exists() or grade.progression_to.exists():
            messages.error(request, 'Cannot delete grade referenced in progression rules.')
            return redirect('employees:grade_list')
        name = grade.name
        grade.delete()
        messages.success(request, f'Grade "{name}" deleted.')
        return redirect('employees:grade_list')
