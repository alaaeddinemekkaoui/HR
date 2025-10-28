from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from apps.employees.models import Employee
from .models import LeaveType, LeaveRequest, EmployeeLeaveBalance, LeaveRequestHistory
from .utils import find_supervisors_for, approvals_scope_q_for_user
from apps.notifications.models import Notification
from .forms import LeaveTypeForm, LeaveRequestForm, EmployeeLeaveBalanceForm


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
            
            # Create history entry for submission
            LeaveRequestHistory.objects.create(
                leave_request=req,
                previous_status='',
                new_status='pending',
                action_by=request.user,
                comment='Leave request submitted'
            )
            
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
        comment = request.POST.get('comment', '').strip()
        req = get_object_or_404(LeaveRequest, pk=pk)
        
        # Check if user is HR Admin (can view but cannot approve/reject)
        is_hr_admin = request.user.groups.filter(name='HR Admin').exists() and not request.user.is_superuser
        if is_hr_admin:
            messages.error(request, 'HR Admin can view requests but cannot approve or reject them. Only direct managers can take action.')
            return redirect('leaves:all_requests')
        
        # Allow IT Admins full access; otherwise ensure the request is within user's supervisory scope
        scope_q = approvals_scope_q_for_user(request.user)
        has_full_access = request.user.is_superuser or request.user.groups.filter(name='IT Admin').exists()
        in_scope = LeaveRequest.objects.filter(pk=req.pk).filter(scope_q).exists()
        
        if not (has_full_access or in_scope):
            messages.error(request, 'You are not allowed to take action on this request.')
            return redirect('leaves:approve')
        
        # Only pending requests can be actioned
        if req.status != 'pending':
            messages.error(request, 'Only pending requests can be approved or rejected.')
            return redirect('leaves:approve')
        
        previous_status = req.status
        
        if action == 'approve':
            req.status = 'approved'
            req.approver = request.user
            req.approved_at = timezone.now()
            req.save()
            
            # Automatically deduct from employee's leave balance
            try:
                req.deduct_from_balance()
            except Exception as e:
                messages.warning(request, f'Leave approved but balance update failed: {str(e)}')
            
            # Create history entry
            LeaveRequestHistory.objects.create(
                leave_request=req,
                previous_status=previous_status,
                new_status='approved',
                action_by=request.user,
                comment=comment or 'Leave request approved'
            )
            
            messages.success(request, f'Leave approved. {req.days} days deducted from balance.')
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
            
            # Create history entry
            LeaveRequestHistory.objects.create(
                leave_request=req,
                previous_status=previous_status,
                new_status='rejected',
                action_by=request.user,
                comment=comment or 'Leave request rejected'
            )
            
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
        
        # Create history entry for deletion
        LeaveRequestHistory.objects.create(
            leave_request=req,
            previous_status=req.status,
            new_status='cancelled',
            action_by=request.user,
            comment='Leave request cancelled by employee'
        )
        
        req.delete()
        messages.success(request, 'Leave request removed.')
        return redirect('leaves:my')


class BalanceResetView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Reset employee leave balance (HR Admin and IT Admin)."""
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name__in=['IT Admin', 'HR Admin']).exists()

    def post(self, request, pk):
        bal = get_object_or_404(EmployeeLeaveBalance, pk=pk)
        # Reset used and recompute closing conservatively
        bal.used = 0
        try:
            bal.closing = (bal.opening or 0) + (bal.accrued or 0) + (bal.carried_over or 0) - (bal.expired or 0) - (bal.used or 0)
        except Exception:
            bal.closing = bal.opening + bal.accrued + bal.carried_over - bal.expired
        bal.save()
        messages.success(request, f'Compteur réinitialisé pour {bal.leave_type.name} ({bal.year}).')
        # Redirect back to leaves page
        return redirect('leaves:my')


class BalanceAdjustView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Allow HR Admin and IT Admin to adjust a specific leave balance."""
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name__in=['IT Admin', 'HR Admin']).exists()

    def get(self, request, pk):
        bal = get_object_or_404(EmployeeLeaveBalance, pk=pk)
        form = EmployeeLeaveBalanceForm(instance=bal)
        return render(request, 'leaves/adjust_balance_form.html', {'form': form, 'balance': bal})

    def post(self, request, pk):
        bal = get_object_or_404(EmployeeLeaveBalance, pk=pk)
        form = EmployeeLeaveBalanceForm(request.POST, instance=bal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Solde mis à jour.')
            return redirect('employees:detail', pk=bal.employee.id)
        return render(request, 'leaves/adjust_balance_form.html', {'form': form, 'balance': bal})


class AllLeaveRequestsView(LoginRequiredMixin, View):
    """View for IT Admin and HR Admin to see ALL leave requests"""
    def get(self, request):
        # Only IT Admin and HR Admin can access
        if not (request.user.is_superuser or request.user.groups.filter(name__in=['HR Admin', 'IT Admin']).exists()):
            messages.error(request, 'You do not have permission to view all leave requests.')
            return redirect('leaves:my')
        
        # Get filter parameters
        status_filter = request.GET.get('status', '')
        employee_search = request.GET.get('employee', '').strip()
        leave_type_filter = request.GET.get('leave_type', '')
        
        # Base query - all requests
        requests = LeaveRequest.objects.select_related('employee', 'leave_type', 'approver').all()
        
        # Apply filters
        if status_filter:
            requests = requests.filter(status=status_filter)
        
        if employee_search:
            requests = requests.filter(
                Q(employee__first_name__icontains=employee_search) |
                Q(employee__last_name__icontains=employee_search) |
                Q(employee__email__icontains=employee_search) |
                Q(employee__employee_id__icontains=employee_search)
            )
        
        if leave_type_filter:
            requests = requests.filter(leave_type_id=leave_type_filter)
        
        requests = requests.order_by('-created_at')
        
        # Check if user is HR Admin (read-only)
        is_hr_readonly = request.user.groups.filter(name='HR Admin').exists() and not request.user.is_superuser
        
        # Get leave types for filter dropdown
        leave_types = LeaveType.objects.filter(is_active=True).order_by('name')
        
        context = {
            'leave_requests': requests,
            'leave_types': leave_types,
            'status_filter': status_filter,
            'employee_search': employee_search,
            'is_hr_readonly': is_hr_readonly,
            'status_choices': LeaveRequest.STATUS_CHOICES
        }
        return render(request, 'leaves/all_requests.html', context)


class LeaveRequestDetailView(LoginRequiredMixin, View):
    """View leave request details with full history"""
    def get(self, request, pk):
        req = get_object_or_404(LeaveRequest, pk=pk)
        
        # Check permission - can view if:
        # 1. IT Admin or HR Admin
        # 2. The employee who submitted it
        # 3. A manager who can see it in their scope
        can_view = False
        
        if request.user.is_superuser or request.user.groups.filter(name__in=['HR Admin', 'IT Admin']).exists():
            can_view = True
        elif req.employee.user == request.user:
            can_view = True
        else:
            scope_q = approvals_scope_q_for_user(request.user)
            if LeaveRequest.objects.filter(pk=req.pk).filter(scope_q).exists():
                can_view = True
        
        if not can_view:
            messages.error(request, 'You do not have permission to view this request.')
            return redirect('leaves:my')
        
        # Get history
        history = req.history.select_related('action_by').order_by('-timestamp')
        
        # Check if user can approve/reject
        is_hr_readonly = request.user.groups.filter(name='HR Admin').exists() and not request.user.is_superuser
        can_approve = not is_hr_readonly and (
            request.user.is_superuser or
            request.user.groups.filter(name='IT Admin').exists() or
            LeaveRequest.objects.filter(pk=req.pk).filter(approvals_scope_q_for_user(request.user)).exists()
        )
        
        context = {
            'leave_request': req,
            'history': history,
            'can_approve': can_approve and req.status == 'pending',
            'is_hr_readonly': is_hr_readonly,
            'is_hr_admin': is_hr_readonly
        }
        return render(request, 'leaves/request_detail.html', context)
