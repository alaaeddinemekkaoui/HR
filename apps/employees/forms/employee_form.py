from django import forms
from django.utils import timezone
from ..models import Employee, Direction, Division, Service, Grade, Position, Departement, Filiere


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'ppr', 'first_name', 'last_name', 'cin', 'email', 'phone',
            'date_of_birth', 'address', 'direction', 'division', 'service',
            'departement', 'filiere',
            'position', 'grade', 'echelle', 'hors_echelle', 'echelon',
            'contract_type', 'hire_date', 'contract_start_date', 'contract_end_date',
            'titularisation_date', 'status'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matricule'}),
            'ppr': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PPR (optionnel)'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'cin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CIN'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0612345678 ou +212612345678'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'division': forms.Select(attrs={'class': 'form-select'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'departement': forms.Select(attrs={'class': 'form-select'}),
            'filiere': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'echelle': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '11', 'placeholder': '1-11'}),
            'hors_echelle': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'echelon': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10', 'placeholder': '1-10'}),
            'contract_type': forms.Select(attrs={'class': 'form-select'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'titularisation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'employee_id': 'Matricule',
            'ppr': 'PPR',
            'first_name': 'Pr�nom',
            'last_name': 'Nom',
            'cin': 'CIN',
            'email': 'Email',
            'phone': 'T�l�phone',
            'date_of_birth': 'Date de naissance',
            'address': 'Adresse',
            'direction': 'Direction (requis)',
            'division': 'Division (optionnel)',
            'service': 'Service (optionnel)',
            'departement': 'D�partement (optionnel)',
            'filiere': 'Fili�re (optionnel)',
            'position': 'Fonction',
            'grade': 'Grade',
            'echelle': '�chelle',
            'hors_echelle': 'Hors �chelle',
            'echelon': '�chelon',
            'contract_type': 'Type de contrat',
            'hire_date': 'Date de recrutement',
            'contract_start_date': 'D�but de contrat',
            'contract_end_date': 'Fin de contrat',
            'titularisation_date': 'Date de titularisation',
            'status': 'Statut',
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = Employee.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Un employ� avec cet email existe d�j�.')
        return email
    
    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        qs = Employee.objects.filter(employee_id=employee_id)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Un employ� avec ce matricule existe d�j�.')
        return employee_id
    
    def clean_cin(self):
        cin = self.cleaned_data.get('cin')
        qs = Employee.objects.filter(cin=cin)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Un employ� avec ce CIN existe d�j�.')
        return cin
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob >= timezone.now().date():
            raise forms.ValidationError('La date de naissance doit �tre dans le pass�.')
        return dob
    
    def clean_hire_date(self):
        hire_date = self.cleaned_data.get('hire_date')
        if hire_date and hire_date > timezone.now().date():
            raise forms.ValidationError('La date de recrutement ne peut pas �tre dans le futur.')
        return hire_date
    
    def clean(self):
        cleaned_data = super().clean()
        echelle = cleaned_data.get('echelle')
        hors_echelle = cleaned_data.get('hors_echelle')
        direction = cleaned_data.get('direction')
        division = cleaned_data.get('division')
        service = cleaned_data.get('service')
        
        if hors_echelle and echelle:
            raise forms.ValidationError('Un employ� ne peut pas avoir � la fois une �chelle et �tre hors �chelle.')
        # Organizational consistency
        if division and direction and division.direction_id != direction.id:
            self.add_error('division', "La division s�lectionn�e n�appartient pas � la direction choisie.")
        if service:
            if service.division:
                # Service under a division; ensure division/direction match
                if division and service.division_id != division.id:
                    self.add_error('service', 'Le service s�lectionn� n�appartient pas � la division choisie.')
                if direction and service.division.direction_id != direction.id:
                    self.add_error('service', "Le service s�lectionn� n�appartient pas � la direction choisie.")
            elif service.direction:
                # Service attached directly to a direction; division should be empty or consistent
                if division:
                    self.add_error('service', 'Ce service est rattach� directement � une direction; laissez la division vide.')
                if direction and service.direction_id != direction.id:
                    self.add_error('service', "Le service s�lectionn� n''appartient pas � la direction choisie.")
        
        # D�partement and Fili�re validation
        departement = cleaned_data.get('departement')
        filiere = cleaned_data.get('filiere')
        
        # Fili�re must belong to D�partement
        if filiere and departement and filiere.departement_id != departement.id:
            self.add_error('filiere', 'La fili�re s�lectionn�e n''appartient pas au d�partement choisi.')
        
        # If fili�re is selected, d�partement must be selected
        if filiere and not departement:
            self.add_error('filiere', 'Vous devez s�lectionner un d�partement pour affecter une fili�re.')
        
        return cleaned_data

