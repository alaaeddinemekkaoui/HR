from django import forms
from ..models import EmploymentHistory


class EmploymentHistoryForm(forms.ModelForm):
    class Meta:
        model = EmploymentHistory
        fields = [
            'change_type', 'effective_date', 'contract_start_date', 
            'contract_end_date', 'retirement_date', 'post_retirement_contract',
            'note', 'document_reference'
        ]
        widgets = {
            'change_type': forms.Select(attrs={'class': 'form-select'}),
            'effective_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'retirement_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'post_retirement_contract': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'document_reference': forms.TextInput(attrs={'class': 'form-control'}),
        }


class GradeChangeForm(forms.Form):
    """Specialized form for recording grade/échelle/échelon changes"""
    effective_date = forms.DateField(
        label='Date effective',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    previous_grade = forms.CharField(
        label='Grade précédent',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    new_grade = forms.ModelChoiceField(
        queryset=None,
        label='Nouveau grade',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )
    previous_echelle = forms.IntegerField(
        required=False,
        label='Échelle précédente',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    new_echelle = forms.IntegerField(
        required=False,
        label='Nouvelle échelle',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '11'})
    )
    previous_echelon = forms.IntegerField(
        required=False,
        label='Échelon précédent',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    new_echelon = forms.IntegerField(
        required=False,
        label='Nouvel échelon',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10'})
    )
    document_reference = forms.CharField(
        required=False,
        label='Référence document',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    note = forms.CharField(
        required=False,
        label='Notes',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Always set the queryset, even if employee is None
        from ..models import Grade
        self.fields['new_grade'].queryset = Grade.objects.filter(is_active=True).order_by('name')
        
        # Set initial values if employee is provided
        if employee:
            self.fields['previous_grade'].initial = str(employee.grade) if employee.grade else ''
            self.fields['previous_echelle'].initial = employee.echelle
            self.fields['previous_echelon'].initial = employee.echelon


class ContractForm(forms.Form):
    """Specialized form for recording contract changes"""
    change_type = forms.ChoiceField(
        choices=[
            ('contract', 'Nouveau Contrat'),
            ('contract_renewal', 'Renouvellement de Contrat'),
        ],
        label='Type',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    effective_date = forms.DateField(
        label='Date effective',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    contract_start_date = forms.DateField(
        label='Date début contrat',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    contract_end_date = forms.DateField(
        required=False,
        label='Date fin contrat (optionnel)',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        help_text='Laisser vide pour contrat indéterminé'
    )
    document_reference = forms.CharField(
        required=False,
        label='Référence document',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    note = forms.CharField(
        required=False,
        label='Notes',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('contract_start_date')
        end = cleaned_data.get('contract_end_date')
        
        if start and end and end <= start:
            raise forms.ValidationError('La date de fin doit être après la date de début.')
        
        return cleaned_data
