from django import forms
from ..models import GradeProgressionRule

class GradeProgressionRuleForm(forms.ModelForm):
    class Meta:
        model = GradeProgressionRule
        fields = ['source_grade', 'target_grade', 'years_with_exam', 'years_without_exam', 'description', 'is_active']
        widgets = {
            'source_grade': forms.Select(attrs={'class': 'form-select'}),
            'target_grade': forms.Select(attrs={'class': 'form-select'}),
            'years_with_exam': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'years_without_exam': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        src = cleaned.get('source_grade')
        tgt = cleaned.get('target_grade')
        if src and tgt and src == tgt:
            self.add_error('target_grade', 'Source and target grade must be different.')
        if src and tgt and src.category != tgt.category:
            self.add_error('target_grade', 'Source and target must be in the same grade category (e.g., Ingénieur → Ingénieur).')
        if not cleaned.get('years_with_exam') and not cleaned.get('years_without_exam'):
            raise forms.ValidationError('Provide at least one of: years with exam or without exam.')
        return cleaned
