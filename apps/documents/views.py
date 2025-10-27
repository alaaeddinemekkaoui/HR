from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from apps.employees.models import Employee
from apps.leaves.models import LeaveRequest
from apps.leaves.utils import find_supervisors_for, approvals_scope_q_for_user
from django.db.models import Q
from django.template import Template, Context
import datetime
from .models import DocumentTemplate
from .forms import DocumentTemplateForm

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


def user_is_hr_or_admin(user: User) -> bool:
    return user.is_superuser or user.groups.filter(name__in=['IT Admin', 'HR Admin', 'HR']).exists()


class AttestationTravailView(LoginRequiredMixin, View):
    def get(self, request, employee_id: int):
        emp = get_object_or_404(Employee, pk=employee_id)
        # Permissions: HR/Admin can view any; otherwise only self
        if not user_is_hr_or_admin(request.user):
            if not hasattr(request.user, 'employee_profile') or request.user.employee_profile.id != emp.id:
                return HttpResponseForbidden('Not allowed')
        context = {
            'employee': emp,
            'today': timezone.now().date(),
        }
        return render(request, 'documents/attestation_travail.html', context)


class DecisionCongeView(LoginRequiredMixin, View):
    def get(self, request, leave_id: int):
        leave = get_object_or_404(LeaveRequest, pk=leave_id)
        # Permissions: owner, HR/Admin, or supervisor within scope
        allowed = False
        if user_is_hr_or_admin(request.user):
            allowed = True
        elif hasattr(request.user, 'employee_profile') and leave.employee_id == request.user.employee_profile.id:
            allowed = True
        else:
            scope_q = approvals_scope_q_for_user(request.user)
            if scope_q != Q(pk__in=[]) and LeaveRequest.objects.filter(scope_q, pk=leave.id).exists():
                allowed = True
        if not allowed:
            return HttpResponseForbidden('Not allowed')

        # Get supervisor for signature (prefer immediate supervisor)
        supervisor_user = None
        sup_users = find_supervisors_for(leave.employee)
        if sup_users:
            supervisor_user = sup_users[0]
        supervisor_emp = getattr(supervisor_user, 'employee_profile', None) if supervisor_user else None
        context = {
            'leave': leave,
            'employee': leave.employee,
            'supervisor': supervisor_emp,
            'today': timezone.now().date(),
        }
        return render(request, 'documents/decision_conge.html', context)


class AttestationSalaireView(LoginRequiredMixin, View):
    def get(self, request, employee_id: int):
        emp = get_object_or_404(Employee, pk=employee_id)
        # Permissions: HR/Admin can view any; otherwise only self
        if not user_is_hr_or_admin(request.user):
            if not hasattr(request.user, 'employee_profile') or request.user.employee_profile.id != emp.id:
                return HttpResponseForbidden('Not allowed')
        # Show a small form to input salary details if not provided
        gross = request.GET.get('gross')
        net = request.GET.get('net')
        if gross and net:
            context = {
                'employee': emp,
                'gross': gross,
                'net': net,
                'today': timezone.now().date(),
            }
            return render(request, 'documents/attestation_salaire.html', context)
        return render(request, 'documents/attestation_salaire_form.html', {'employee': emp})

    def post(self, request, employee_id: int):
        emp = get_object_or_404(Employee, pk=employee_id)
        if not user_is_hr_or_admin(request.user):
            if not hasattr(request.user, 'employee_profile') or request.user.employee_profile.id != emp.id:
                return HttpResponseForbidden('Not allowed')
        gross = request.POST.get('gross')
        net = request.POST.get('net')
        context = {
            'employee': emp,
            'gross': gross,
            'net': net,
            'today': timezone.now().date(),
        }
        return render(request, 'documents/attestation_salaire.html', context)


class HROnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return user_is_hr_or_admin(self.request.user)


class DocumentsHomeView(LoginRequiredMixin, View):
    def get(self, request):
        emp = getattr(request.user, 'employee_profile', None)
        templates = None
        if user_is_hr_or_admin(request.user):
            templates = DocumentTemplate.objects.filter(is_active=True)
        return render(request, 'documents/home.html', {
            'employee': emp,
            'templates': templates,
        })


class TemplateListView(LoginRequiredMixin, HROnlyMixin, View):
    def get(self, request):
        qs = DocumentTemplate.objects.all()
        return render(request, 'documents/templates_list.html', {'templates': qs})


class TemplateCreateView(LoginRequiredMixin, HROnlyMixin, View):
    def get(self, request):
        form = DocumentTemplateForm()
        return render(request, 'documents/template_form.html', {'form': form, 'mode': 'create'})

    def post(self, request):
        form = DocumentTemplateForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.updated_by = request.user
            obj.save()
            return redirect('documents:template_list')
        return render(request, 'documents/template_form.html', {'form': form, 'mode': 'create'})


class TemplateEditView(LoginRequiredMixin, HROnlyMixin, View):
    def get(self, request, pk: int):
        obj = get_object_or_404(DocumentTemplate, pk=pk)
        form = DocumentTemplateForm(instance=obj)
        return render(request, 'documents/template_form.html', {'form': form, 'mode': 'edit', 'template_obj': obj})

    def post(self, request, pk: int):
        obj = get_object_or_404(DocumentTemplate, pk=pk)
        form = DocumentTemplateForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.updated_by = request.user
            obj.save()
            return redirect('documents:template_list')
        return render(request, 'documents/template_form.html', {'form': form, 'mode': 'edit', 'template_obj': obj})


class TemplateDeleteView(LoginRequiredMixin, HROnlyMixin, View):
    def post(self, request, pk: int):
        obj = get_object_or_404(DocumentTemplate, pk=pk)
        obj.delete()
        return redirect('documents:template_list')


class TemplateRenderView(LoginRequiredMixin, View):
    """Render a dynamic template using Django template engine.
    For HR/Admin only if hr_only=True. Accepts employee context via querystring (?employee_id=) or URL.
    """
    def get(self, request, slug: str, employee_id: int = None):
        tmpl = get_object_or_404(DocumentTemplate, slug=slug, is_active=True)
        if tmpl.hr_only and not user_is_hr_or_admin(request.user):
            return HttpResponseForbidden('Not allowed')

        emp = None
        provided_id = employee_id or request.GET.get('employee_id')
        choose = request.GET.get('choose')
        if provided_id:
            try:
                emp = Employee.objects.get(pk=provided_id)
            except Employee.DoesNotExist:
                # Fallback to current user's employee if available
                emp = getattr(request.user, 'employee_profile', None)
        
        # If still no employee selected, default to current user's employee if present
        if not emp:
            emp = getattr(request.user, 'employee_profile', None)

        # If HR/Admin explicitly wants to choose (or has no employee profile), show picker
        if (choose and user_is_hr_or_admin(request.user)) or (user_is_hr_or_admin(request.user) and not emp):
            return render(request, 'documents/template_select_employee.html', {'template_obj': tmpl})

        # If non-HR has no employee profile, forbid
        if not emp:
            return HttpResponseForbidden('Employee profile required')

        # Optional supervisor (for signature blocks)
        supervisor_user = None
        supervisor_emp = None
        if emp:
            sup_users = find_supervisors_for(emp)
            if sup_users:
                supervisor_user = sup_users[0]
                supervisor_emp = getattr(supervisor_user, 'employee_profile', None)

        ctx = {
            'employee': emp,
            'supervisor': supervisor_emp,
            'today': timezone.now().date(),
            'request': request,
        }
        # Preprocess simple sandbox tokens like [name], [cin], [position], [organization], [today]
        source = tmpl.content
        def safe(val):
            return '' if val is None else str(val)
        token_map = {
            '[name]': safe(getattr(emp, 'full_name', None) if emp else None),
            '[cin]': safe(getattr(emp, 'cin', None) if emp else None),
            '[position]': safe(getattr(getattr(emp, 'position', None), 'name', None) if emp else None),
            '[organization]': safe(getattr(emp, 'organizational_path', None) if emp else None),
            '[grade]': safe(getattr(emp, 'grade_display', None) if emp else None),
            '[today]': safe(ctx['today']),
            '[supervisor_name]': safe(getattr(supervisor_emp, 'full_name', None) if supervisor_emp else None),
            '[supervisor_position]': safe(getattr(getattr(supervisor_emp, 'position', None), 'name', None) if supervisor_emp else None),
        }
        for token, value in token_map.items():
            source = source.replace(token, value)

        # Then allow Django template variables like {{ employee.full_name }} to render too
        rendered = Template(source).render(Context(ctx))
        return render(request, 'documents/render.html', {
            'template_obj': tmpl,
            'rendered': rendered,
        })


# PDF Download Views
class AttestationTravailPDFView(LoginRequiredMixin, View):
    def get(self, request, employee_id: int):
        if not WEASYPRINT_AVAILABLE:
            return HttpResponse("PDF generation not available. Install weasyprint.", status=500)
        
        emp = get_object_or_404(Employee, pk=employee_id)
        # Permissions: HR/Admin can view any; otherwise only self
        if not user_is_hr_or_admin(request.user):
            if not hasattr(request.user, 'employee_profile') or request.user.employee_profile.id != emp.id:
                return HttpResponseForbidden('Not allowed')
        
        context = {
            'employee': emp,
            'today': timezone.now().date(),
        }
        html_string = render_to_string('documents/attestation_travail.html', context)
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="attestation_travail_{emp.employee_id}.pdf"'
        return response


class DecisionCongePDFView(LoginRequiredMixin, View):
    def get(self, request, leave_id: int):
        if not WEASYPRINT_AVAILABLE:
            return HttpResponse("PDF generation not available. Install weasyprint.", status=500)
        
        leave = get_object_or_404(LeaveRequest, pk=leave_id)
        # Permissions: owner, HR/Admin, or supervisor within scope
        allowed = False
        if user_is_hr_or_admin(request.user):
            allowed = True
        elif hasattr(request.user, 'employee_profile') and leave.employee_id == request.user.employee_profile.id:
            allowed = True
        else:
            scope_q = approvals_scope_q_for_user(request.user)
            if scope_q != Q(pk__in=[]) and LeaveRequest.objects.filter(scope_q, pk=leave.id).exists():
                allowed = True
        if not allowed:
            return HttpResponseForbidden('Not allowed')

        # Get supervisor for signature
        supervisor_user = None
        sup_users = find_supervisors_for(leave.employee)
        if sup_users:
            supervisor_user = sup_users[0]
        supervisor_emp = getattr(supervisor_user, 'employee_profile', None) if supervisor_user else None
        
        context = {
            'leave': leave,
            'employee': leave.employee,
            'supervisor': supervisor_emp,
            'today': timezone.now().date(),
        }
        html_string = render_to_string('documents/decision_conge.html', context)
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="decision_conge_{leave.id}.pdf"'
        return response


class AttestationSalairePDFView(LoginRequiredMixin, View):
    def get(self, request, employee_id: int):
        if not WEASYPRINT_AVAILABLE:
            return HttpResponse("PDF generation not available. Install weasyprint.", status=500)
        
        emp = get_object_or_404(Employee, pk=employee_id)
        # Permissions: HR/Admin can view any; otherwise only self
        if not user_is_hr_or_admin(request.user):
            if not hasattr(request.user, 'employee_profile') or request.user.employee_profile.id != emp.id:
                return HttpResponseForbidden('Not allowed')
        
        gross = request.GET.get('gross')
        net = request.GET.get('net')
        
        if not gross or not net:
            return HttpResponse("Missing salary parameters (gross, net)", status=400)
        
        context = {
            'employee': emp,
            'gross': gross,
            'net': net,
            'today': timezone.now().date(),
        }
        html_string = render_to_string('documents/attestation_salaire.html', context)
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf = html.write_pdf()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="attestation_salaire_{emp.employee_id}.pdf"'
        return response


class AdminDocumentGeneratorView(UserPassesTestMixin, View):
    """View for IT Admin/HR Admin to generate documents for any employee"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name__in=['IT Admin', 'HR Admin']).exists()
    
    def get(self, request):
        search_query = request.GET.get('search', '').strip()
        employees = []
        
        if search_query:
            # Search by name, employee_id, or PPR
            employees = Employee.objects.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(employee_id__icontains=search_query) |
                Q(ppr__icontains=search_query)
            ).select_related('position', 'grade', 'direction', 'division', 'service')[:20]
        
        # Get all active document templates
        templates = DocumentTemplate.objects.filter(is_active=True).order_by('name')
        
        context = {
            'search_query': search_query,
            'employees': employees,
            'templates': templates,
        }
        return render(request, 'documents/admin_generator.html', context)


