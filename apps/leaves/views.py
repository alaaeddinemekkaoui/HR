from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from apps.employees.models import Employee
from .models import LeaveType, LeaveRequest, EmployeeLeaveBalance
from .utils import find_supervisors_for, approvals_scope_q_for_user
from apps.notifications.models import Notification
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
            # Notify supervisors
            supervisors = find_supervisors_for(employee)
            for u in supervisors:
                Notification.objects.create(
                    recipient=u,
                    actor=request.user,
                    category='leave_request',
                    title=f"Leave request from {employee.full_name}",
                    message=f"{req.leave_type.name}: {req.start_date} → {req.end_date} ({req.days} days)",
                    url='/leaves/approve/'
                )
            # Notify the requesting employee (confirmation)
            if employee.user:
                Notification.objects.create(
                    recipient=employee.user,
                    actor=request.user,
                    category='leave_request',
                    title='Leave request submitted',
                    message=f"{req.leave_type.name}: {req.start_date} → {req.end_date} ({req.days} days)",
                    url='/leaves/my/'
                )
            messages.success(request, f'Request submitted for {req.days} day(s).')
            return redirect('leaves:my')
        return render(request, 'leaves/request_form.html', {'form': form})


class LeaveApproveListView(LoginRequiredMixin, View):
    def get(self, request):
        scope_q = approvals_scope_q_for_user(request.user)
        # scope_q empty Q() means full access; pk__in=[] means none
        pending = (LeaveRequest.objects
                   .filter(status='pending')
                   .filter(scope_q)
                   .select_related('employee','leave_type'))
        return render(request, 'leaves/approve_list.html', {'pending': pending})


class LeaveApproveActionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        action = request.POST.get('action')
        req = get_object_or_404(LeaveRequest, pk=pk)
        # Allow admins full access; otherwise ensure the request is within user's supervisory scope
        from django.db.models import Q
        scope_q = approvals_scope_q_for_user(request.user)
        has_full_access = isinstance(scope_q, Q) and scope_q.children == []  # Q() => admins
        in_scope = LeaveRequest.objects.filter(pk=req.pk).filter(scope_q).exists()
        if not (has_full_access or in_scope):
            messages.error(request, 'You are not allowed to take action on this request.')
            return redirect('leaves:approve')
        # Only pending requests can be actioned
        if req.status != 'pending':
            messages.error(request, 'Only pending requests can be approved or rejected.')
            return redirect('leaves:approve')
        if action == 'approve':
            req.status = 'approved'
            req.approver = request.user
            req.approved_at = timezone.now()
            req.save()
            # TODO: Update balances accordingly (accrual/carryover logic can be implemented in a scheduled job)
            messages.success(request, 'Leave approved.')
            # Notify employee
            if req.employee.user:
                Notification.objects.create(
                    recipient=req.employee.user,
                    actor=request.user,
                    category='leave_update',
                    title='Leave request approved',
                    message=f"{req.leave_type.name}: {req.start_date} → {req.end_date} ({req.days} days)",
                    url='/leaves/my/'
                )
        elif action == 'reject':
            req.status = 'rejected'
            req.approver = request.user
            req.approved_at = timezone.now()
            req.save()
            messages.info(request, 'Leave rejected.')
            # Notify employee
            if req.employee.user:
                Notification.objects.create(
                    recipient=req.employee.user,
                    actor=request.user,
                    category='leave_update',
                    title='Leave request rejected',
                    message=f"{req.leave_type.name}: {req.start_date} → {req.end_date} ({req.days} days)",
                    url='/leaves/my/'
                )
        else:
            messages.error(request, 'Unknown action.')
        return redirect('leaves:approve')

class LeaveRequestDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        req = get_object_or_404(LeaveRequest, pk=pk, employee__user=request.user)
        if req.status != 'pending':
            messages.error(request, 'Only pending requests can be removed.')
            return redirect('leaves:my')
        req.delete()
        messages.success(request, 'Leave request removed.')
        return redirect('leaves:my')
