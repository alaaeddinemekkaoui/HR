from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.models import User
from ..models import Employee, Direction, Division, Service
from ..forms import EmployeeForm
from ..controllers.employee_controller import (
    list_employees,
    delete_employee,
)


class EmployeeCreateAccountView(PermissionRequiredMixin, View):
    permission_required = 'auth.add_user'
    
    def post(self, request, pk: int):
        employee = get_object_or_404(Employee, pk=pk)
        if employee.user:
            messages.warning(request, f'{employee.full_name} already has a user account.')
            return redirect(reverse('employees:detail', kwargs={'pk': pk}))
        
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect(reverse('employees:detail', kwargs={'pk': pk}))
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return redirect(reverse('employees:detail', kwargs={'pk': pk}))
        
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
            return redirect(reverse('employees:detail', kwargs={'pk': pk}))
        
        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=employee.email,
            first_name=employee.first_name,
            last_name=employee.last_name
        )
        employee.user = user
        employee.save()
        
        messages.success(request, f'User account created for {employee.full_name} with username "{username}".')
        return redirect(reverse('employees:detail', kwargs={'pk': pk}))


class EmployeeModifyAccountView(PermissionRequiredMixin, View):
    permission_required = 'auth.change_user'
    
    def post(self, request, pk: int):
        employee = get_object_or_404(Employee, pk=pk)
        if not employee.user:
            messages.warning(request, f'{employee.full_name} does not have a user account.')
            return redirect(reverse('employees:detail', kwargs={'pk': pk}))
        
        user = employee.user
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        new_password = request.POST.get('new_password', '').strip()
        new_password_confirm = request.POST.get('new_password_confirm', '').strip()
        
        if not username:
            messages.error(request, 'Username is required.')
            return redirect(reverse('employees:detail', kwargs={'pk': pk}))
        
        # Check username uniqueness if changed
        if username != user.username and User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
            return redirect(reverse('employees:detail', kwargs={'pk': pk}))
        
        # Check password match if provided
        if new_password:
            if new_password != new_password_confirm:
                messages.error(request, 'New passwords do not match.')
                return redirect(reverse('employees:detail', kwargs={'pk': pk}))
            user.set_password(new_password)
        
        # Update user
        user.username = username
        user.email = email
        user.is_active = is_active
        user.save()
        
        messages.success(request, f'User account updated for {employee.full_name}.')
        return redirect(reverse('employees:detail', kwargs={'pk': pk}))


class EmployeeDeleteAccountView(PermissionRequiredMixin, View):
    permission_required = 'auth.delete_user'
    
    def post(self, request, pk: int):
        employee = get_object_or_404(Employee, pk=pk)
        if not employee.user:
            messages.warning(request, f'{employee.full_name} does not have a user account.')
            return redirect(reverse('employees:detail', kwargs={'pk': pk}))
        
        username = employee.user.username
        employee.user.delete()
        employee.user = None
        employee.save()
        
        messages.success(request, f'User account "{username}" deleted for {employee.full_name}.')
        return redirect(reverse('employees:detail', kwargs={'pk': pk}))


class EmployeeListView(View):
    def get(self, request):
        employees = list_employees()

        # Scope restriction for regular users (see only coworkers in the same direct assignment)
        if not request.user.is_superuser and not request.user.groups.filter(name__in=['HR Admin', 'IT Admin']).exists():
            emp = getattr(request.user, 'employee_profile', None)
            scope_q = Q(user=request.user)  # always include self
            if emp:
                if emp.service_id:
                    scope_q |= Q(service_id=emp.service_id)
                elif emp.division_id:
                    scope_q |= Q(division_id=emp.division_id, service__isnull=True)
                elif emp.direction_id:
                    scope_q |= Q(direction_id=emp.direction_id, division__isnull=True, service__isnull=True)
            else:
                # No employee profile: restrict to none except self (which likely won't match if no link)
                pass
            employees = employees.filter(scope_q)
        
        # Search functionality (support both 'search' and 'q' parameters)
        search_query = (request.GET.get('search') or request.GET.get('q') or '').strip()
        if search_query:
            terms = [t for t in search_query.split() if t]
            # Build a combined Q: AND across terms, OR across fields within each term
            base_q = Q()
            initialized = False
            for term in terms:
                term_q = (
                    Q(first_name__icontains=term) |
                    Q(last_name__icontains=term) |
                    Q(email__icontains=term) |
                    Q(employee_id__icontains=term) |
                    Q(ppr__icontains=term) |
                    Q(cin__icontains=term) |
                    Q(phone__icontains=term) |
                    Q(position__name__icontains=term) |
                    Q(grade__name__icontains=term) |
                    Q(direction__name__icontains=term) |
                    Q(division__name__icontains=term) |
                    Q(service__name__icontains=term)
                )
                base_q = term_q if not initialized else (base_q & term_q)
                initialized = True
            # Add exact match boost for numeric-only queries
            if search_query.isdigit():
                base_q = base_q | Q(employee_id=search_query) | Q(ppr=search_query)
            employees = employees.filter(base_q)
        
        # Filter by status
        status_filter = request.GET.get('status', '')
        if status_filter:
            employees = employees.filter(status=status_filter)

        # Organizational filters
        direction_id = request.GET.get('direction')
        division_id = request.GET.get('division')
        service_id = request.GET.get('service')

        if direction_id:
            employees = employees.filter(direction_id=direction_id)
        if division_id:
            employees = employees.filter(division_id=division_id)
        if service_id:
            employees = employees.filter(service_id=service_id)
        
        # Pagination with custom page size
        page_size = request.GET.get('page_size', '10')
        try:
            page_size = int(page_size)
            if page_size not in [5, 10, 25, 50, 100]:
                page_size = 10
        except (ValueError, TypeError):
            page_size = 10
            
        paginator = Paginator(employees, page_size)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Dropdown choices (limit to user's scope for regular users)
        if request.user.is_superuser or request.user.groups.filter(name__in=['HR Admin', 'IT Admin']).exists():
            directions = Direction.objects.filter(is_active=True).order_by('name')
            divisions = Division.objects.filter(is_active=True).order_by('name')
            services = Service.objects.filter(is_active=True).order_by('name')
        else:
            emp = getattr(request.user, 'employee_profile', None)
            if emp and emp.service_id:
                directions = Direction.objects.filter(pk=emp.direction_id, is_active=True)
                divisions = Division.objects.filter(pk=emp.division_id, is_active=True)
                services = Service.objects.filter(pk=emp.service_id, is_active=True)
            elif emp and emp.division_id:
                directions = Direction.objects.filter(pk=emp.direction_id, is_active=True)
                divisions = Division.objects.filter(pk=emp.division_id, is_active=True)
                services = Service.objects.filter(division_id=emp.division_id, is_active=True)
            elif emp and emp.direction_id:
                directions = Direction.objects.filter(pk=emp.direction_id, is_active=True)
                divisions = Division.objects.filter(direction_id=emp.direction_id, is_active=True)
                services = Service.objects.filter(direction_id=emp.direction_id, is_active=True)
            else:
                directions = Direction.objects.none()
                divisions = Division.objects.none()
                services = Service.objects.none()
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'direction_id': int(direction_id) if direction_id else None,
            'division_id': int(division_id) if division_id else None,
            'service_id': int(service_id) if service_id else None,
            'directions': directions,
            'divisions': divisions,
            'services': services,
            'status_choices': Employee.STATUS_CHOICES,
        }
        return render(request, 'employees/list.html', context)


class EmployeeDetailView(View):
    def get(self, request, pk: int):
        employee = get_object_or_404(Employee, pk=pk)
        # Restrict visibility to scope for non-admin users
        if not request.user.is_superuser and not request.user.groups.filter(name__in=['HR Admin', 'IT Admin']).exists():
            my_emp = getattr(request.user, 'employee_profile', None)
            allowed = False
            if my_emp and my_emp.id == employee.id:
                allowed = True
            else:
                scope_q = Q()
                if my_emp:
                    if my_emp.service_id:
                        scope_q = Q(service_id=my_emp.service_id)
                    elif my_emp.division_id:
                        scope_q = Q(division_id=my_emp.division_id, service__isnull=True)
                    elif my_emp.direction_id:
                        scope_q = Q(direction_id=my_emp.direction_id, division__isnull=True, service__isnull=True)
                if scope_q and Employee.objects.filter(pk=employee.pk).filter(scope_q).exists():
                    allowed = True
            if not allowed:
                messages.error(request, 'You are not allowed to view this employee.')
                return redirect('employees:list')
        return render(request, 'employees/detail.html', {'employee': employee})


class EmployeeCreateView(PermissionRequiredMixin, View):
    permission_required = 'employees.add_employee'
    raise_exception = True
    
    def get(self, request):
        form = EmployeeForm()
        return render(request, 'employees/form.html', {'form': form, 'mode': 'create'})

    def post(self, request):
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            # Auto-provision user account
            try:
                email = employee.email.strip().lower()
                username = email
                user = User.objects.filter(username=username).first()
                if not user:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        first_name=employee.first_name,
                        last_name=employee.last_name,
                        password='rabat2025'
                    )
                    messages.info(request, f'Login created for {email} with temporary password.')
                else:
                    messages.info(request, f'User {email} already exists; linked to employee.')
                # Link
                if not employee.user:
                    employee.user = user
                    employee.save(update_fields=['user'])
            except Exception as ex:
                messages.warning(request, f'Employee saved, but user creation/linking failed: {ex}')
            messages.success(request, 'Employee created successfully!')
            return redirect(reverse('employees:list'))
        else:
            messages.error(request, 'Please correct the errors below.')
        return render(request, 'employees/form.html', {'form': form, 'mode': 'create'})


class EmployeeUpdateView(PermissionRequiredMixin, View):
    permission_required = 'employees.change_employee'
    raise_exception = True
    def get(self, request, pk: int):
        employee = get_object_or_404(Employee, pk=pk)
        form = EmployeeForm(instance=employee)
        return render(request, 'employees/form.html', {'form': form, 'mode': 'edit', 'employee': employee})

    def post(self, request, pk: int):
        employee = get_object_or_404(Employee, pk=pk)
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully!')
            return redirect(reverse('employees:detail', kwargs={'pk': pk}))
        else:
            messages.error(request, 'Please correct the errors below.')
        return render(request, 'employees/form.html', {'form': form, 'mode': 'edit', 'employee': employee})


class EmployeeDeleteView(PermissionRequiredMixin, View):
    permission_required = 'employees.delete_employee'
    raise_exception = True
    def post(self, request, pk: int):
        employee = get_object_or_404(Employee, pk=pk)
        employee_name = employee.full_name
        delete_employee(employee)
        messages.success(request, f'Employee {employee_name} deleted successfully!')
        return redirect(reverse('employees:list'))
