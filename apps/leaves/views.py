from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from apps.employees.models import Employee
from .models import LeaveType, LeaveRequest, EmployeeLeaveBalance
from .forms import LeaveTypeForm, LeaveRequestForm


class LeaveTypeListView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'leaves.view_leavetype'
    def get(self, request):
        types_ = LeaveType.objects.all().order_by('name')
        return render(request, 'leaves/types_list.html', {'types': types_})


class LeaveTypeCreateView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'leaves.add_leavetype'
    def get(self, request):
        return render(request, 'leaves/type_form.html', {'form': LeaveTypeForm(), 'mode':'create'})
    def post(self, request):
        form = LeaveTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave type created.')
            return redirect('leaves:types')
        return render(request, 'leaves/type_form.html', {'form': form, 'mode':'create'})


class LeaveTypeEditView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'leaves.change_leavetype'
    def get(self, request, pk):
        lt = get_object_or_404(LeaveType, pk=pk)
        return render(request, 'leaves/type_form.html', {'form': LeaveTypeForm(instance=lt), 'mode':'edit', 'obj': lt})
    def post(self, request, pk):
        lt = get_object_or_404(LeaveType, pk=pk)
        form = LeaveTypeForm(request.POST, instance=lt)
        if form.is_valid():
            form.save()
            messages.success(request, 'Leave type updated.')
            return redirect('leaves:types')
        return render(request, 'leaves/type_form.html', {'form': form, 'mode':'edit', 'obj': lt})


class MyLeavesView(LoginRequiredMixin, View):
    def get(self, request):
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            messages.error(request, 'No employee profile linked to your account.')
            return redirect('employees:list')
        year = timezone.now().year
        balances = EmployeeLeaveBalance.objects.filter(employee=employee, year__in=[year, year-1, year-2]).select_related('leave_type')
        requests = LeaveRequest.objects.filter(employee=employee).select_related('leave_type').order_by('-created_at')[:20]
        return render(request, 'leaves/my_leaves.html', {'balances': balances, 'requests': requests, 'year': year})


class LeaveRequestCreateView(LoginRequiredMixin, View):
    def get(self, request):
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            messages.error(request, 'No employee profile linked to your account.')
            return redirect('employees:list')
        form = LeaveRequestForm()
        return render(request, 'leaves/request_form.html', {'form': form})
    def post(self, request):
        employee = getattr(request.user, 'employee_profile', None)
        if not employee:
            messages.error(request, 'No employee profile linked to your account.')
            return redirect('employees:list')
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.employee = employee
            req.compute_days()
            req.save()
            messages.success(request, f'Request submitted for {req.days} day(s).')
            return redirect('leaves:my')
        return render(request, 'leaves/request_form.html', {'form': form})


class LeaveApproveListView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'leaves.change_leaverequest'
    def get(self, request):
        pending = LeaveRequest.objects.filter(status='pending').select_related('employee','leave_type')
        return render(request, 'leaves/approve_list.html', {'pending': pending})


class LeaveApproveActionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'leaves.change_leaverequest'
    def post(self, request, pk):
        action = request.POST.get('action')
        req = get_object_or_404(LeaveRequest, pk=pk)
        if action == 'approve':
            req.status = 'approved'
            req.approver = request.user
            req.approved_at = timezone.now()
            req.save()
            # TODO: Update balances accordingly (accrual/carryover logic can be implemented in a scheduled job)
            messages.success(request, 'Leave approved.')
        elif action == 'reject':
            req.status = 'rejected'
            req.approver = request.user
            req.approved_at = timezone.now()
            req.save()
            messages.info(request, 'Leave rejected.')
        else:
            messages.error(request, 'Unknown action.')
        return redirect('leaves:approve')
