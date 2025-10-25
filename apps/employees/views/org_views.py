from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import IntegrityError
from ..models import Direction, Division, Service
from ..forms.org_forms import DirectionForm, DivisionForm, ServiceForm


class ITAdminOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_superuser or user.groups.filter(name='IT Admin').exists())


class DirectionListView(LoginRequiredMixin, View):
    def get(self, request):
        directions = Direction.objects.all().order_by('name')
        return render(request, 'employees/org/directions.html', {'directions': directions})


class DirectionCreateView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        form = DirectionForm()
        return render(request, 'employees/org/direction_form.html', {'form': form, 'mode': 'create'})

    def post(self, request):
        form = DirectionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Direction created.')
            return redirect('employees:org_directions')
        return render(request, 'employees/org/direction_form.html', {'form': form, 'mode': 'create'})


class DirectionEditView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request, pk):
        direction = get_object_or_404(Direction, pk=pk)
        form = DirectionForm(instance=direction)
        return render(request, 'employees/org/direction_form.html', {'form': form, 'mode': 'edit', 'obj': direction})

    def post(self, request, pk):
        direction = get_object_or_404(Direction, pk=pk)
        form = DirectionForm(request.POST, instance=direction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Direction updated.')
            return redirect('employees:org_directions')
        return render(request, 'employees/org/direction_form.html', {'form': form, 'mode': 'edit', 'obj': direction})


class DirectionDeleteView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def post(self, request, pk):
        direction = get_object_or_404(Direction, pk=pk)
        try:
            direction_name = direction.name
            direction.delete()
            messages.success(request, f'Direction ''{direction_name}'' deleted successfully.')
        except IntegrityError:
            messages.error(request, f'Cannot delete Direction ''{direction.name}''. It has related employees, divisions, or services.')
        return redirect('employees:org_directions')


class DivisionListView(LoginRequiredMixin, View):
    def get(self, request):
        divisions = Division.objects.select_related('direction').all().order_by('direction__name', 'name')
        return render(request, 'employees/org/divisions.html', {'divisions': divisions})


class DivisionCreateView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        form = DivisionForm()
        return render(request, 'employees/org/division_form.html', {'form': form, 'mode': 'create'})

    def post(self, request):
        form = DivisionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Division created.')
            return redirect('employees:org_divisions')
        return render(request, 'employees/org/division_form.html', {'form': form, 'mode': 'create'})


class DivisionEditView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request, pk):
        division = get_object_or_404(Division, pk=pk)
        form = DivisionForm(instance=division)
        return render(request, 'employees/org/division_form.html', {'form': form, 'mode': 'edit', 'obj': division})

    def post(self, request, pk):
        division = get_object_or_404(Division, pk=pk)
        form = DivisionForm(request.POST, instance=division)
        if form.is_valid():
            form.save()
            messages.success(request, 'Division updated.')
            return redirect('employees:org_divisions')
        return render(request, 'employees/org/division_form.html', {'form': form, 'mode': 'edit', 'obj': division})


class DivisionDeleteView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def post(self, request, pk):
        division = get_object_or_404(Division, pk=pk)
        try:
            division_name = division.name
            division.delete()
            messages.success(request, f'Division ''{division_name}'' deleted successfully.')
        except IntegrityError:
            messages.error(request, f'Cannot delete Division ''{division.name}''. It has related employees or services.')
        return redirect('employees:org_divisions')


class ServiceListView(LoginRequiredMixin, View):
    def get(self, request):
        services = Service.objects.select_related('direction', 'division', 'division__direction').all().order_by('name')
        return render(request, 'employees/org/services.html', {'services': services})


class ServiceCreateView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        form = ServiceForm()
        return render(request, 'employees/org/service_form.html', {'form': form, 'mode': 'create'})

    def post(self, request):
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service created.')
            return redirect('employees:org_services')
        return render(request, 'employees/org/service_form.html', {'form': form, 'mode': 'create'})


class ServiceEditView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        form = ServiceForm(instance=service)
        return render(request, 'employees/org/service_form.html', {'form': form, 'mode': 'edit', 'obj': service})

    def post(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, 'Service updated.')
            return redirect('employees:org_services')
        return render(request, 'employees/org/service_form.html', {'form': form, 'mode': 'edit', 'obj': service})


class ServiceDeleteView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def post(self, request, pk):
        service = get_object_or_404(Service, pk=pk)
        try:
            service_name = service.name
            service.delete()
            messages.success(request, f'Service ''{service_name}'' deleted successfully.')
        except IntegrityError:
            messages.error(request, f'Cannot delete Service ''{service.name}''. It has related employees.')
        return redirect('employees:org_services')
