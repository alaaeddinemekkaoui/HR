from django import forms
from ..models import Direction, Division, Service, Departement, Filiere

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


class DepartementForm(forms.ModelForm):
    class Meta:
        model = Departement
        fields = ['direction', 'division', 'service', 'name', 'code', 'description', 'is_active']
        widgets = {
            'direction': forms.Select(attrs={'class': 'form-select'}),
            'division': forms.Select(attrs={'class': 'form-select'}),
            'service': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'direction': 'Direction (défaut: DE)',
            'division': 'Division (optionnel)',
            'service': 'Service (optionnel)',
            'name': 'Nom',
            'code': 'Code',
            'description': 'Description',
            'is_active': 'Actif',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default direction to DE if creating new
        if not self.instance.pk:
            try:
                de = Direction.objects.get(code='DE')
                self.fields['direction'].initial = de
            except Direction.DoesNotExist:
                pass


class FiliereForm(forms.ModelForm):
    class Meta:
        model = Filiere
        fields = ['departement', 'name', 'code', 'description', 'is_active']
        widgets = {
            'departement': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'departement': 'Département',
            'name': 'Nom',
            'code': 'Code',
            'description': 'Description',
            'is_active': 'Actif',
        }
