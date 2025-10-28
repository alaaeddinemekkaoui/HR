"""
Deployment Forms
Forms for managing employee travel allowances and mission orders
"""
from django import forms
from django.core.exceptions import ValidationError
from ..models import DeploymentForfaitaire, DeploymentReal, OrdreMission, GradeDeploymentRate, Employee
from datetime import date


class GradeDeploymentRateForm(forms.ModelForm):
    """Form for managing default deployment rates per grade"""
    
    class Meta:
        model = GradeDeploymentRate
        fields = ['grade', 'daily_rate', 'monthly_rate', 'effective_date', 'is_active', 'notes']
        widgets = {
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'daily_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'monthly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DeploymentForfaitaireForm(forms.ModelForm):
    """
    Form for requesting fixed monthly deployment allowance
    NO approval needed - generates document for signature
    For HR/Admin: can create for themselves or other employees
    """
    # Choice field for HR/Admin
    FOR_CHOICES = [
        ('me', 'Pour moi'),
        ('other', 'Pour un autre employé'),
    ]
    
    for_who = forms.ChoiceField(
        choices=FOR_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Créer pour',
        required=False,
        initial='me'
    )
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Employé',
        required=False
    )
    
    class Meta:
        model = DeploymentForfaitaire
        fields = ['month', 'amount', 'notes', 'document_reference']
        widgets = {
            'month': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'month',
                'placeholder': 'YYYY-MM'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Montant en DH'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes ou justification (optionnel)'
            }),
            'document_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Référence du document (optionnel)'
            }),
        }
        labels = {
            'month': 'Mois concerné',
            'amount': 'Montant (DH)',
            'notes': 'Notes',
            'document_reference': 'Référence document',
        }
        help_texts = {
            'month': 'Le document sera généré automatiquement pour signature',
        }
    
    def __init__(self, *args, current_employee=None, is_hr_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_employee = current_employee
        self.is_hr_admin = is_hr_admin
        
        # Only show for_who field for HR/Admin
        if not is_hr_admin:
            self.fields.pop('for_who', None)
            self.fields.pop('employee', None)
        else:
            # Order employees by name for easier selection
            self.fields['employee'].queryset = Employee.objects.all().order_by('first_name', 'last_name')
        
        # Set default amount based on employee's grade if creating new
        if current_employee and not self.instance.pk and not is_hr_admin:
            rate = GradeDeploymentRate.get_current_rate(current_employee.grade)
            if rate:
                self.fields['amount'].initial = rate.monthly_rate
                self.fields['amount'].help_text = f'Montant par défaut pour {current_employee.grade.name}: {rate.monthly_rate} DH/mois'
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.is_hr_admin:
            for_who = cleaned_data.get('for_who')
            employee = cleaned_data.get('employee')
            
            if for_who == 'other' and not employee:
                raise ValidationError("Veuillez sélectionner un employé")
            
            # Set employee based on choice
            if for_who == 'me':
                cleaned_data['selected_employee'] = self.current_employee
            else:
                cleaned_data['selected_employee'] = employee
                
            # Update amount default based on selected employee
            if cleaned_data.get('selected_employee'):
                rate = GradeDeploymentRate.get_current_rate(cleaned_data['selected_employee'].grade)
                if rate and not cleaned_data.get('amount'):
                    cleaned_data['amount'] = rate.monthly_rate
        else:
            cleaned_data['selected_employee'] = self.current_employee
        
        return cleaned_data
    
    def clean_month(self):
        """Ensure month is first day of month and validate uniqueness"""
        month = self.cleaned_data.get('month')
        if month:
            # Force to first day of month
            month = month.replace(day=1)
            
            # Check for duplicate if creating new or changing month
            if self.employee and (not self.instance.pk or self.instance.month != month):
                exists = DeploymentForfaitaire.objects.filter(
                    employee=self.employee,
                    month=month
                ).exists()
                if exists:
                    raise ValidationError(f'Une demande existe déjà pour {month.strftime("%B %Y")}.')
        
        return month
    
    def clean_amount(self):
        """Validate amount is positive"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError('Le montant doit être supérieur à 0.')
        return amount


class OrdreMissionForm(forms.ModelForm):
    """
    Form for requesting mission order (travel authorization)
    Requires hierarchy approval - generates document upon approval
    For HR/Admin: can create for themselves or other employees
    """
    # Choice field for HR/Admin
    FOR_CHOICES = [
        ('me', 'Pour moi'),
        ('other', 'Pour un autre employé'),
    ]
    
    for_who = forms.ChoiceField(
        choices=FOR_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Créer pour',
        required=False,
        initial='me'
    )
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Employé',
        required=False
    )
    
    class Meta:
        model = OrdreMission
        fields = [
            'start_date', 'end_date', 'location', 'purpose',
            'ordre_document', 'notes'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville, pays'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Objet de la mission'}),
            'ordre_document': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.jpg,.png'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notes additionnelles (optionnel)'
            }),
        }
        labels = {
            'start_date': 'Date de départ',
            'end_date': 'Date de retour',
            'location': 'Lieu de mission',
            'purpose': 'Objet de la mission',
            'ordre_document': 'Document de preuve (optionnel)',
            'notes': 'Notes',
        }
        help_texts = {
            'ordre_document': 'Télécharger un document de support si disponible (optionnel)',
            'start_date': 'Le document sera généré après approbation de la hiérarchie',
        }
    
    def __init__(self, *args, current_employee=None, is_hr_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_employee = current_employee
        self.is_hr_admin = is_hr_admin
        
        # Only show for_who field for HR/Admin
        if not is_hr_admin:
            self.fields.pop('for_who', None)
            self.fields.pop('employee', None)
        else:
            # Order employees by name for easier selection
            self.fields['employee'].queryset = Employee.objects.all().order_by('first_name', 'last_name')
    
    def clean(self):
        """Validate dates and employee selection"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError('La date de retour doit être après la date de départ.')
        
        # Handle employee selection for HR/Admin
        if self.is_hr_admin:
            for_who = cleaned_data.get('for_who')
            employee = cleaned_data.get('employee')
            
            if for_who == 'other' and not employee:
                raise ValidationError("Veuillez sélectionner un employé")
            
            # Set employee based on choice
            if for_who == 'me':
                cleaned_data['selected_employee'] = self.current_employee
            else:
                cleaned_data['selected_employee'] = employee
        else:
            cleaned_data['selected_employee'] = self.current_employee
        
        return cleaned_data


class DeploymentRealForm(forms.ModelForm):
    """
    Form for actual deployment expenses (HR/Admin ONLY)
    NO approval needed - administrative tracking, generates document
    """
    # Choice field for HR/Admin
    FOR_CHOICES = [
        ('me', 'Pour moi'),
        ('other', 'Pour un autre employé'),
    ]
    
    for_who = forms.ChoiceField(
        choices=FOR_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Créer pour',
        required=False,
        initial='me'
    )
    
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Employé',
        required=False
    )
    
    class Meta:
        model = DeploymentReal
        fields = [
            'start_date', 'end_date', 'location', 'purpose',
            'daily_rate', 'number_of_days', 'total_amount',
            'notes', 'document_reference'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville, pays'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Objet de la mission'}),
            'daily_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Taux journalier (optionnel si montant total direct)'
            }),
            'number_of_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Calculé automatiquement'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Montant total en DH'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes, frais additionnels, etc. (optionnel)'
            }),
            'document_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ordre de mission, factures, etc. (optionnel)'
            }),
        }
        labels = {
            'start_date': 'Date de départ',
            'end_date': 'Date de retour',
            'location': 'Lieu de mission',
            'purpose': 'Objet de la mission',
            'daily_rate': 'Taux journalier (DH)',
            'number_of_days': 'Nombre de jours',
            'total_amount': 'Montant total (DH)',
            'notes': 'Notes',
            'document_reference': 'Référence document',
        }
        help_texts = {
            'total_amount': 'Le document sera généré automatiquement pour signature',
        }
    
    def __init__(self, *args, current_employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_employee = current_employee
        
        # Order employees by name for easier selection
        self.fields['employee'].queryset = Employee.objects.all().order_by('first_name', 'last_name')
        
        # Set default daily rate based on current employee's grade if creating new
        if current_employee and not self.instance.pk:
            rate = GradeDeploymentRate.get_current_rate(current_employee.grade)
            if rate:
                self.fields['daily_rate'].initial = rate.daily_rate
                self.fields['daily_rate'].help_text = f'Taux par défaut pour {current_employee.grade.name}: {rate.daily_rate} DH/jour'
    
    def clean(self):
        """Validate dates, employee selection and calculate fields"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        daily_rate = cleaned_data.get('daily_rate')
        number_of_days = cleaned_data.get('number_of_days')
        total_amount = cleaned_data.get('total_amount')
        
        # Handle employee selection
        for_who = cleaned_data.get('for_who')
        employee = cleaned_data.get('employee')
        
        if for_who == 'other' and not employee:
            raise ValidationError("Veuillez sélectionner un employé")
        
        # Set employee based on choice
        if for_who == 'me':
            cleaned_data['selected_employee'] = self.current_employee
        else:
            cleaned_data['selected_employee'] = employee
        
        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError('La date de retour doit être après la date de départ.')
            
            # Auto-calculate number of days
            if not number_of_days:
                calculated_days = (end_date - start_date).days + 1
                cleaned_data['number_of_days'] = calculated_days
                number_of_days = calculated_days
        
        # Validate financial fields
        if not total_amount and not (daily_rate and number_of_days):
            raise ValidationError('Vous devez fournir soit le montant total, soit le taux journalier et le nombre de jours.')
        
        # Auto-calculate total if daily rate provided
        if daily_rate and number_of_days and not total_amount:
            cleaned_data['total_amount'] = daily_rate * number_of_days
        
        return cleaned_data


class OrdreMissionReviewForm(forms.Form):
    """Form for hierarchy to approve/reject mission orders"""
    
    STATUS_CHOICES = [
        ('approved', 'Approuver'),
        ('rejected', 'Rejeter'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Décision'
    )
    review_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Notes d\'examen',
        help_text='Commentaires ou justification de la décision'
    )



class GradeDeploymentRateForm(forms.ModelForm):
    """Form for managing default deployment rates per grade"""
    
    class Meta:
        model = GradeDeploymentRate
        fields = ['grade', 'daily_rate', 'monthly_rate', 'effective_date', 'is_active', 'notes']
        widgets = {
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'daily_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'monthly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DeploymentForfaitaireForm(forms.ModelForm):
    """Form for requesting fixed monthly deployment allowance"""
    
    class Meta:
        model = DeploymentForfaitaire
        fields = ['month', 'amount', 'notes', 'document_reference']
        widgets = {
            'month': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'month',
                'placeholder': 'YYYY-MM'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Montant en DH'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes ou justification (optionnel)'
            }),
            'document_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Référence du document (optionnel)'
            }),
        }
        labels = {
            'month': 'Mois concerné',
            'amount': 'Montant (DH)',
            'notes': 'Notes',
            'document_reference': 'Référence document',
        }
    
    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        
        # Set default amount based on employee's grade if creating new
        if employee and not self.instance.pk:
            rate = GradeDeploymentRate.get_current_rate(employee.grade)
            if rate:
                self.fields['amount'].initial = rate.monthly_rate
                self.fields['amount'].help_text = f'Montant par défaut pour {employee.grade.name}: {rate.monthly_rate} DH/mois'
    
    def clean_month(self):
        """Ensure month is first day of month and validate uniqueness"""
        month = self.cleaned_data.get('month')
        if month:
            # Force to first day of month
            month = month.replace(day=1)
            
            # Check for duplicate if creating new or changing month
            if self.employee and (not self.instance.pk or self.instance.month != month):
                exists = DeploymentForfaitaire.objects.filter(
                    employee=self.employee,
                    month=month
                ).exists()
                if exists:
                    raise ValidationError(f'Une demande existe déjà pour {month.strftime("%B %Y")}.')
        
        return month
    
    def clean_amount(self):
        """Validate amount is positive"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError('Le montant doit être supérieur à 0.')
        return amount


class DeploymentRealForm(forms.ModelForm):
    """Form for requesting actual deployment expenses"""
    
    class Meta:
        model = DeploymentReal
        fields = [
            'start_date', 'end_date', 'location', 'purpose',
            'daily_rate', 'number_of_days', 'total_amount',
            'notes', 'document_reference'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville, pays'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Objet de la mission'}),
            'daily_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Taux journalier (optionnel si montant total direct)'
            }),
            'number_of_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Calculé automatiquement'
            }),
            'total_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Montant total en DH'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes, frais additionnels, etc. (optionnel)'
            }),
            'document_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ordre de mission, factures, etc. (optionnel)'
            }),
        }
        labels = {
            'start_date': 'Date de départ',
            'end_date': 'Date de retour',
            'location': 'Lieu de mission',
            'purpose': 'Objet de la mission',
            'daily_rate': 'Taux journalier (DH)',
            'number_of_days': 'Nombre de jours',
            'total_amount': 'Montant total (DH)',
            'notes': 'Notes',
            'document_reference': 'Référence document',
        }
    
    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        
        # Set default daily rate based on employee's grade if creating new
        if employee and not self.instance.pk:
            rate = GradeDeploymentRate.get_current_rate(employee.grade)
            if rate:
                self.fields['daily_rate'].initial = rate.daily_rate
                self.fields['daily_rate'].help_text = f'Taux par défaut pour {employee.grade.name}: {rate.daily_rate} DH/jour'
    
    def clean(self):
        """Validate dates and calculate fields"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        daily_rate = cleaned_data.get('daily_rate')
        number_of_days = cleaned_data.get('number_of_days')
        total_amount = cleaned_data.get('total_amount')
        
        # Validate date range
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError('La date de retour doit être après la date de départ.')
            
            # Auto-calculate number of days
            if not number_of_days:
                calculated_days = (end_date - start_date).days + 1
                cleaned_data['number_of_days'] = calculated_days
                number_of_days = calculated_days
        
        # Validate financial fields
        if not total_amount and not (daily_rate and number_of_days):
            raise ValidationError('Vous devez fournir soit le montant total, soit le taux journalier et le nombre de jours.')
        
        # Auto-calculate total if daily rate provided
        if daily_rate and number_of_days and not total_amount:
            cleaned_data['total_amount'] = daily_rate * number_of_days
        
        return cleaned_data


class DeploymentReviewForm(forms.Form):
    """Form for HR Admin to approve/reject deployments"""
    
    STATUS_CHOICES = [
        ('approved', 'Approuver'),
        ('rejected', 'Rejeter'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Décision'
    )
    review_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Notes d\'examen',
        help_text='Commentaires ou justification de la décision'
    )
