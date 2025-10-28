"""
Deployment Views
Views for managing employee travel allowances:
- DeploymentForfaitaire: Fixed monthly allowance (no approval)
- OrdreMission: Travel authorization (requires approval)
- DeploymentReal: Actual expenses (HR/Admin only, no approval)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum, Count
from datetime import date
from ..models import (
    Employee, 
    DeploymentForfaitaire, 
    DeploymentReal, 
    OrdreMission,
    GradeDeploymentRate
)
from ..forms import (
    DeploymentForfaitaireForm,
    DeploymentRealForm,
    OrdreMissionForm,
    OrdreMissionReviewForm,
    GradeDeploymentRateForm
)


class DeploymentListView(LoginRequiredMixin, View):
    """List all deployments for current user (all 3 types)"""
    
    def get(self, request):
        # Get employee profile
        try:
            employee = request.user.employee_profile
        except:
            messages.error(request, "Vous n'avez pas de profil employé.")
            return redirect('dashboard')
        
        # Get all three types of deployments
        forfaitaires = employee.deployments_forfaitaire.all().order_by('-month')
        reals = employee.deployments_real.all().order_by('-start_date')
        ordres = employee.ordres_mission.all().order_by('-start_date')
        
        # Calculate statistics (no approval for forfaitaire/real, only for ordres)
        stats = {
            'forfaitaire_total': forfaitaires.aggregate(Sum('amount'))['amount__sum'] or 0,
            'real_total': reals.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
            'forfaitaire_count': forfaitaires.count(),
            'real_count': reals.count(),
            'ordres_pending': ordres.filter(status='pending').count(),
            'ordres_approved': ordres.filter(status='approved').count(),
        }
        
        context = {
            'forfaitaires': forfaitaires[:10],  # Last 10
            'reals': reals[:10],  # Last 10
            'ordres': ordres[:10],  # Last 10
            'stats': stats,
            'employee': employee,
        }
        return render(request, 'employees/deployments/my_deployments.html', context)


class DeploymentForfaitaireCreateView(UserPassesTestMixin, View):
    """Create new forfaitaire deployment - HR/Admin only, no approval required"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(
            name__in=['IT Admin', 'HR Admin']
        ).exists()
    
    def get(self, request):
        try:
            employee = request.user.employee_profile
        except:
            messages.error(request, "Vous n'avez pas de profil employé.")
            return redirect('dashboard')
        
        is_hr_admin = self.test_func()
        form = DeploymentForfaitaireForm(current_employee=employee, is_hr_admin=is_hr_admin)
        
        context = {
            'form': form,
            'employee': employee,
            'deployment_type': 'forfaitaire',
            'is_hr_admin': is_hr_admin,
        }
        return render(request, 'employees/deployments/deployment_form.html', context)
    
    def post(self, request):
        try:
            employee = request.user.employee_profile
        except:
            messages.error(request, "Vous n'avez pas de profil employé.")
            return redirect('dashboard')
        
        is_hr_admin = self.test_func()
        form = DeploymentForfaitaireForm(request.POST, current_employee=employee, is_hr_admin=is_hr_admin)
        
        if form.is_valid():
            deployment = form.save(commit=False)
            selected_employee = form.cleaned_data.get('selected_employee')
            deployment.employee = selected_employee
            deployment.requested_by = request.user
            
            # Store default amount for reference
            rate = GradeDeploymentRate.get_current_rate(selected_employee.grade)
            if rate:
                deployment.default_amount = rate.monthly_rate
            
            deployment.save()
            
            messages.success(request, f"Déplacement forfaitaire créé pour {deployment.employee.full_name} - {deployment.month.strftime('%B %Y')}! Document à générer et faire signer.")
            
            # Redirect based on for_who choice
            for_who = form.cleaned_data.get('for_who', 'me')
            if for_who == 'me':
                return redirect('employees:deployments_list')
            else:
                return redirect('employees:deployments_approval')
        
        context = {
            'form': form,
            'employee': employee,
            'deployment_type': 'forfaitaire',
            'is_hr_admin': is_hr_admin,
        }
        return render(request, 'employees/deployments/deployment_form.html', context)


class DeploymentRealCreateView(UserPassesTestMixin, View):
    """Create new real deployment - HR/Admin only, no approval required"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(
            name__in=['IT Admin', 'HR Admin']
        ).exists()
    
    def get(self, request):
        try:
            employee = request.user.employee_profile
        except:
            messages.error(request, "Vous n'avez pas de profil employé.")
            return redirect('dashboard')
        
        form = DeploymentRealForm(current_employee=employee)
        
        context = {
            'form': form,
            'deployment_type': 'real',
        }
        return render(request, 'employees/deployments/deployment_form.html', context)
    
    def post(self, request):
        try:
            employee = request.user.employee_profile
        except:
            messages.error(request, "Vous n'avez pas de profil employé.")
            return redirect('dashboard')
        
        form = DeploymentRealForm(request.POST, current_employee=employee)
        
        if form.is_valid():
            deployment = form.save(commit=False)
            selected_employee = form.cleaned_data.get('selected_employee')
            deployment.employee = selected_employee
            deployment.created_by = request.user
            
            # Store default daily rate for reference
            rate = GradeDeploymentRate.get_current_rate(selected_employee.grade)
            if rate:
                deployment.default_daily_rate = rate.daily_rate
            
            deployment.save()
            
            messages.success(request, f"Déplacement réel créé pour {deployment.employee.full_name} - {deployment.location}! Document à générer et faire signer.")
            
            # Redirect based on for_who choice
            for_who = form.cleaned_data.get('for_who', 'me')
            if for_who == 'me':
                return redirect('employees:deployments_list')
            else:
                return redirect('employees:deployments_approval')
        
        context = {
            'form': form,
            'deployment_type': 'real',
        }
        return render(request, 'employees/deployments/deployment_form.html', context)


class OrdreMissionCreateView(LoginRequiredMixin, View):
    """Create new ordre de mission - requires approval (or for HR for other employees)"""
    
    def get(self, request):
        try:
            employee = request.user.employee_profile
        except:
            messages.error(request, "Vous n'avez pas de profil employé.")
            return redirect('dashboard')
        
        is_hr_admin = request.user.is_superuser or request.user.groups.filter(
            name__in=['IT Admin', 'HR Admin']
        ).exists()
        
        form = OrdreMissionForm(current_employee=employee, is_hr_admin=is_hr_admin)
        
        context = {
            'form': form,
            'employee': employee,
            'is_hr_admin': is_hr_admin,
        }
        return render(request, 'employees/deployments/ordre_mission_form.html', context)
    
    def post(self, request):
        try:
            employee = request.user.employee_profile
        except:
            messages.error(request, "Vous n'avez pas de profil employé.")
            return redirect('dashboard')
        
        is_hr_admin = request.user.is_superuser or request.user.groups.filter(
            name__in=['IT Admin', 'HR Admin']
        ).exists()
        
        form = OrdreMissionForm(request.POST, request.FILES, current_employee=employee, is_hr_admin=is_hr_admin)
        
        if form.is_valid():
            ordre = form.save(commit=False)
            selected_employee = form.cleaned_data.get('selected_employee')
            ordre.employee = selected_employee
            ordre.requested_by = request.user
            ordre.save()
            
            messages.success(request, f"Ordre de mission créé pour {ordre.employee.full_name} - {ordre.location}! En attente d'approbation de la hiérarchie.")
            
            # Redirect based on for_who choice
            for_who = form.cleaned_data.get('for_who', 'me')
            if for_who == 'me' or not is_hr_admin:
                return redirect('employees:deployments_list')
            else:
                return redirect('employees:deployments_approval')
        
        context = {
            'form': form,
            'employee': employee,
            'is_hr_admin': is_hr_admin,
        }
        return render(request, 'employees/deployments/ordre_mission_form.html', context)


class OrdreMissionApprovalListView(UserPassesTestMixin, View):
    """List all pending ordres de mission for hierarchy approval"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(
            name__in=['IT Admin', 'HR Admin']
        ).exists()
    
    def get(self, request):
        # Get all pending ordres
        ordres_pending = OrdreMission.objects.filter(
            status='pending'
        ).select_related('employee', 'requested_by').order_by('requested_at')
        
        # Get recently reviewed
        ordres_reviewed = OrdreMission.objects.filter(
            status__in=['approved', 'rejected']
        ).select_related('employee', 'reviewed_by').order_by('-reviewed_at')[:20]
        
        # Also show all deployments for HR overview
        forfaitaires = DeploymentForfaitaire.objects.select_related('employee').order_by('-month')[:20]
        reals = DeploymentReal.objects.select_related('employee').order_by('-start_date')[:20]
        
        context = {
            'ordres_pending': ordres_pending,
            'ordres_reviewed': ordres_reviewed,
            'forfaitaires': forfaitaires,
            'reals': reals,
        }
        return render(request, 'employees/deployments/approval_list.html', context)


class OrdreMissionReviewView(UserPassesTestMixin, View):
    """Approve or reject an ordre de mission"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(
            name__in=['IT Admin', 'HR Admin']
        ).exists()
    
    def get(self, request, pk):
        ordre = get_object_or_404(OrdreMission, pk=pk)
        
        if not ordre.can_approve():
            messages.warning(request, "Cet ordre de mission ne peut plus être examiné.")
            return redirect('employees:deployments_approval')
        
        form = OrdreMissionReviewForm()
        
        context = {
            'ordre': ordre,
            'form': form,
        }
        return render(request, 'employees/deployments/ordre_review.html', context)
    
    def post(self, request, pk):
        ordre = get_object_or_404(OrdreMission, pk=pk)
        
        if not ordre.can_approve():
            messages.warning(request, "Cet ordre de mission ne peut plus être examiné.")
            return redirect('employees:deployments_approval')
        
        form = OrdreMissionReviewForm(request.POST)
        
        if form.is_valid():
            ordre.status = form.cleaned_data['status']
            ordre.review_notes = form.cleaned_data.get('review_notes', '')
            ordre.reviewed_by = request.user
            ordre.reviewed_at = timezone.now()
            ordre.save()
            
            status_text = 'approuvé' if ordre.status == 'approved' else 'rejeté'
            messages.success(request, f"Ordre de mission {status_text}!")
            
            if ordre.status == 'approved':
                messages.info(request, "Document d'ordre de mission à générer et faire signer.")
            
            return redirect('employees:deployments_approval')
        
        context = {
            'ordre': ordre,
            'form': form,
        }
        return render(request, 'employees/deployments/ordre_review.html', context)


class GradeDeploymentRateListView(UserPassesTestMixin, View):
    """List and manage grade deployment rates (HR Admin only)"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(
            name__in=['IT Admin', 'HR Admin']
        ).exists()
    
    def get(self, request):
        rates = GradeDeploymentRate.objects.select_related('grade').order_by(
            'grade__name', '-effective_date'
        )
        
        context = {
            'rates': rates,
        }
        return render(request, 'employees/deployments/rate_list.html', context)


class GradeDeploymentRateCreateView(UserPassesTestMixin, View):
    """Create new grade deployment rate"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(
            name__in=['IT Admin', 'HR Admin']
        ).exists()
    
    def get(self, request):
        form = GradeDeploymentRateForm()
        
        context = {
            'form': form,
            'mode': 'create',
        }
        return render(request, 'employees/deployments/rate_form.html', context)
    
    def post(self, request):
        form = GradeDeploymentRateForm(request.POST)
        
        if form.is_valid():
            rate = form.save(commit=False)
            rate.created_by = request.user
            rate.save()
            
            messages.success(request, f"Taux créé pour {rate.grade.name}!")
            return redirect('employees:deployment_rates')
        
        context = {
            'form': form,
            'mode': 'create',
        }
        return render(request, 'employees/deployments/rate_form.html', context)


class GradeDeploymentRateUpdateView(UserPassesTestMixin, View):
    """Update existing grade deployment rate"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(
            name__in=['IT Admin', 'HR Admin']
        ).exists()
    
    def get(self, request, pk):
        rate = get_object_or_404(GradeDeploymentRate, pk=pk)
        form = GradeDeploymentRateForm(instance=rate)
        
        context = {
            'form': form,
            'rate': rate,
            'mode': 'edit',
        }
        return render(request, 'employees/deployments/rate_form.html', context)
    
    def post(self, request, pk):
        rate = get_object_or_404(GradeDeploymentRate, pk=pk)
        form = GradeDeploymentRateForm(request.POST, instance=rate)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Taux mis à jour!")
            return redirect('employees:deployment_rates')
        
        context = {
            'form': form,
            'rate': rate,
            'mode': 'edit',
        }
        return render(request, 'employees/deployments/rate_form.html', context)
