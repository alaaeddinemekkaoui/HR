from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from ..models import Employee, EmploymentHistory
from ..forms import EmploymentHistoryForm, GradeChangeForm, ContractForm


class EmploymentHistoryListView(LoginRequiredMixin, View):
    """Display employment history timeline for an employee"""
    
    def get(self, request, employee_id: int):
        employee = get_object_or_404(Employee, pk=employee_id)
        
        # Check access permissions
        can_view = False
        if request.user.is_superuser or request.user.groups.filter(name__in=['IT Admin', 'HR Admin']).exists():
            can_view = True
        elif hasattr(request.user, 'employee_profile') and request.user.employee_profile.id == employee.id:
            can_view = True
        
        if not can_view:
            messages.error(request, "Vous n'êtes pas autorisé à voir cet historique.")
            return redirect('employees:list')
        
        # Get all history entries ordered by date (most recent first)
        history_entries = employee.employment_history.all().order_by('-effective_date', '-created_at')
        
        context = {
            'employee': employee,
            'history_entries': history_entries,
        }
        return render(request, 'employees/history/history_list.html', context)


class EmploymentHistoryCreateView(UserPassesTestMixin, View):
    """Add a new employment history entry (IT Admin / HR Admin only)"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name__in=['IT Admin', 'HR Admin']).exists()
    
    def get(self, request, employee_id: int):
        employee = get_object_or_404(Employee, pk=employee_id)
        form = EmploymentHistoryForm()
        
        context = {
            'form': form,
            'employee': employee,
            'mode': 'create',
        }
        return render(request, 'employees/history/history_form.html', context)
    
    def post(self, request, employee_id: int):
        employee = get_object_or_404(Employee, pk=employee_id)
        form = EmploymentHistoryForm(request.POST)
        
        if form.is_valid():
            history = form.save(commit=False)
            history.employee = employee
            history.created_by = request.user
            history.save()
            
            messages.success(request, "Entrée d'historique créée avec succès!")
            return redirect(reverse('employees:detail', kwargs={'pk': employee_id}))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        
        context = {
            'form': form,
            'employee': employee,
            'mode': 'create',
        }
        return render(request, 'employees/history/history_form.html', context)


class EmploymentHistoryUpdateView(UserPassesTestMixin, View):
    """Edit an existing employment history entry (IT Admin / HR Admin only)"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name__in=['IT Admin', 'HR Admin']).exists()
    
    def get(self, request, pk: int):
        history = get_object_or_404(EmploymentHistory, pk=pk)
        form = EmploymentHistoryForm(instance=history)
        
        context = {
            'form': form,
            'employee': history.employee,
            'history': history,
            'mode': 'edit',
        }
        return render(request, 'employees/history/history_form.html', context)
    
    def post(self, request, pk: int):
        history = get_object_or_404(EmploymentHistory, pk=pk)
        form = EmploymentHistoryForm(request.POST, instance=history)
        
        if form.is_valid():
            updated_history = form.save(commit=False)
            updated_history.updated_at = timezone.now()
            updated_history.save()
            
            messages.success(request, "Entrée d'historique mise à jour avec succès!")
            return redirect(reverse('employees:detail', kwargs={'pk': history.employee.id}))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        
        context = {
            'form': form,
            'employee': history.employee,
            'history': history,
            'mode': 'edit',
        }
        return render(request, 'employees/history/history_form.html', context)


class EmploymentHistoryDeleteView(UserPassesTestMixin, View):
    """Delete an employment history entry (IT Admin only)"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='IT Admin').exists()
    
    def post(self, request, pk: int):
        history = get_object_or_404(EmploymentHistory, pk=pk)
        employee_id = history.employee.id
        history_summary = history.change_summary
        
        history.delete()
        messages.success(request, f"Entrée d'historique supprimée: {history_summary}")
        return redirect(reverse('employees:detail', kwargs={'pk': employee_id}))


class GradeChangeCreateView(UserPassesTestMixin, View):
    """Specialized view for grade/échelle/échelon changes"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name__in=['IT Admin', 'HR Admin']).exists()
    
    def get(self, request, employee_id: int):
        employee = get_object_or_404(Employee, pk=employee_id)
        
        # Pre-populate form with current values
        initial_data = {
            'previous_grade': employee.grade,
            'previous_echelle': employee.echelle,
            'previous_echelon': employee.echelon,
        }
        form = GradeChangeForm(initial=initial_data)
        
        context = {
            'form': form,
            'employee': employee,
            'mode': 'create',
        }
        return render(request, 'employees/history/grade_change_form.html', context)
    
    def post(self, request, employee_id: int):
        employee = get_object_or_404(Employee, pk=employee_id)
        form = GradeChangeForm(request.POST)
        
        if form.is_valid():
            # Determine change type
            change_type = 'grade'
            if form.cleaned_data.get('new_echelle') and form.cleaned_data.get('new_echelle') != employee.echelle:
                change_type = 'echelle'
            if form.cleaned_data.get('new_echelon') and form.cleaned_data.get('new_echelon') != employee.echelon:
                change_type = 'echelon'
            
            # Create history entry
            history = EmploymentHistory(
                employee=employee,
                change_type=change_type,
                effective_date=form.cleaned_data['effective_date'],
                created_by=request.user,
                notes=form.cleaned_data.get('notes', ''),
                document_reference=form.cleaned_data.get('document_reference', ''),
            )
            
            # Store previous and new values
            history.previous_values = {
                'grade': employee.grade.name if employee.grade else None,
                'echelle': employee.echelle,
                'echelon': employee.echelon,
            }
            
            history.new_values = {
                'grade': form.cleaned_data['new_grade'].name if form.cleaned_data.get('new_grade') else None,
                'echelle': form.cleaned_data.get('new_echelle'),
                'echelon': form.cleaned_data.get('new_echelon'),
            }
            
            history.save()
            
            # Update employee record
            if form.cleaned_data.get('new_grade'):
                employee.grade = form.cleaned_data['new_grade']
            if form.cleaned_data.get('new_echelle'):
                employee.echelle = form.cleaned_data['new_echelle']
            if form.cleaned_data.get('new_echelon'):
                employee.echelon = form.cleaned_data['new_echelon']
            employee.save()
            
            messages.success(request, f"Changement de {change_type} enregistré avec succès!")
            return redirect(reverse('employees:detail', kwargs={'pk': employee_id}))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        
        context = {
            'form': form,
            'employee': employee,
            'mode': 'create',
        }
        return render(request, 'employees/history/grade_change_form.html', context)


class ContractCreateView(UserPassesTestMixin, View):
    """Specialized view for contract management (new, renewal, end)"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name__in=['IT Admin', 'HR Admin']).exists()
    
    def get(self, request, employee_id: int):
        employee = get_object_or_404(Employee, pk=employee_id)
        form = ContractForm()
        
        context = {
            'form': form,
            'employee': employee,
            'mode': 'create',
        }
        return render(request, 'employees/history/contract_form.html', context)
    
    def post(self, request, employee_id: int):
        employee = get_object_or_404(Employee, pk=employee_id)
        form = ContractForm(request.POST)
        
        if form.is_valid():
            # Create history entry
            history = EmploymentHistory(
                employee=employee,
                change_type=form.cleaned_data['contract_type'],
                effective_date=form.cleaned_data['effective_date'],
                contract_start_date=form.cleaned_data['contract_start_date'],
                contract_end_date=form.cleaned_data.get('contract_end_date'),
                created_by=request.user,
                notes=form.cleaned_data.get('notes', ''),
                document_reference=form.cleaned_data.get('document_reference', ''),
            )
            
            # Store contract details in new_values
            history.new_values = {
                'contract_type': form.cleaned_data['contract_type'],
                'contract_start_date': str(form.cleaned_data['contract_start_date']),
                'contract_end_date': str(form.cleaned_data['contract_end_date']) if form.cleaned_data.get('contract_end_date') else None,
            }
            
            history.save()
            
            messages.success(request, "Contrat enregistré avec succès!")
            return redirect(reverse('employees:detail', kwargs={'pk': employee_id}))
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        
        context = {
            'form': form,
            'employee': employee,
            'mode': 'create',
        }
        return render(request, 'employees/history/contract_form.html', context)


class RetirementCreateView(UserPassesTestMixin, View):
    """Specialized view for retirement tracking"""
    
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name__in=['IT Admin', 'HR Admin']).exists()
    
    def get(self, request, employee_id: int):
        employee = get_object_or_404(Employee, pk=employee_id)
        
        context = {
            'employee': employee,
        }
        return render(request, 'employees/history/retirement_form.html', context)
    
    def post(self, request, employee_id: int):
        employee = get_object_or_404(Employee, pk=employee_id)
        
        retirement_date = request.POST.get('retirement_date')
        post_retirement_contract = request.POST.get('post_retirement_contract') == 'on'
        notes = request.POST.get('notes', '').strip()
        document_reference = request.POST.get('document_reference', '').strip()
        
        if not retirement_date:
            messages.error(request, "La date de retraite est obligatoire.")
            return render(request, 'employees/history/retirement_form.html', {'employee': employee})
        
        # Create history entry
        history = EmploymentHistory(
            employee=employee,
            change_type='retirement',
            effective_date=retirement_date,
            retirement_date=retirement_date,
            post_retirement_contract=post_retirement_contract,
            created_by=request.user,
            notes=notes,
            document_reference=document_reference,
        )
        
        history.new_values = {
            'retirement_date': retirement_date,
            'post_retirement_contract': post_retirement_contract,
        }
        
        history.save()
        
        # Update employee status to retired if applicable
        if not post_retirement_contract:
            employee.status = 'retired'
            employee.save()
        
        messages.success(request, "Retraite enregistrée avec succès!")
        return redirect(reverse('employees:detail', kwargs={'pk': employee_id}))
