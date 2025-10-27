from django import forms
from .models import LeaveType, LeaveRequest
from .models import EmployeeLeaveBalance
from django import forms


class EmployeeLeaveBalanceForm(forms.ModelForm):
    class Meta:
        model = EmployeeLeaveBalance
        fields = ['opening', 'accrued', 'used', 'carried_over', 'expired', 'closing']
        widgets = {
            'opening': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'accrued': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'used': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'carried_over': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'expired': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'closing': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class LeaveTypeForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = ['code','name','description','paid','annual_days','prorata_monthly','carry_over_years','exclude_weekends','requires_approval','is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class':'form-control'}),
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.TextInput(attrs={'class':'form-control'}),
            'paid': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'annual_days': forms.NumberInput(attrs={'class':'form-control','step':'0.01'}),
            'prorata_monthly': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'carry_over_years': forms.NumberInput(attrs={'class':'form-control','min':'0'}),
            'exclude_weekends': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'requires_approval': forms.CheckboxInput(attrs={'class':'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type','start_date','end_date','reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class':'form-select'}),
            'start_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'end_date': forms.DateInput(attrs={'class':'form-control','type':'date'}),
            'reason': forms.Textarea(attrs={'class':'form-control','rows':3}),
        }

    def clean(self):
        cleaned = super().clean()
        sd = cleaned.get('start_date')
        ed = cleaned.get('end_date')
        if sd and ed and ed < sd:
            self.add_error('end_date', 'End date must be after start date.')
        return cleaned
