from django import forms
from ..models import Direction, Division, Service

class DirectionForm(forms.ModelForm):
    class Meta:
        model = Direction
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DivisionForm(forms.ModelForm):
    class Meta:
        model = Division
        fields = ['direction', 'name', 'code', 'description', 'is_active']
        widgets = {
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['direction', 'division', 'name', 'code', 'description', 'is_active']
        widgets = {
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'division': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        direction = cleaned.get('direction')
        division = cleaned.get('division')
        # Exactly one must be set
        if bool(direction) == bool(division):
            raise forms.ValidationError('Sélectionnez soit une direction soit une division (mais pas les deux).')
        # If division set, ensure its direction matches selected direction if any
        return cleaned
