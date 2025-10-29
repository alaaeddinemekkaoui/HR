from django import forms
from .models import ElectronicSignature, SignatureStatus, StampArtifact


class SignatureForm(forms.ModelForm):
    """Form for capturing electronic signature"""
    
    signature_method = forms.ChoiceField(
        choices=[
            ('draw', 'Draw Signature'),
            ('type', 'Type Full Name'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='draw'
    )
    
    accept_terms = forms.BooleanField(
        required=True,
        label='I certify that this is my electronic signature and I agree to sign this document',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = ElectronicSignature
        fields = ['signature_image', 'signature_text', 'comments']
        widgets = {
            'signature_image': forms.HiddenInput(),
            'signature_text': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Type your full name'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional comments (e.g., conditions, notes)'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        signature_method = cleaned_data.get('signature_method')
        signature_image = cleaned_data.get('signature_image')
        signature_text = cleaned_data.get('signature_text')
        
        if signature_method == 'draw' and not signature_image:
            raise forms.ValidationError('Please draw your signature in the canvas above.')
        
        if signature_method == 'type' and not signature_text:
            raise forms.ValidationError('Please type your full name.')
        
        return cleaned_data


class RejectSignatureForm(forms.Form):
    """Form for rejecting a signature request"""
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please provide a reason for rejection...',
            'required': True
        }),
        label='Reason for Rejection'
    )


class SignatureWorkflowForm(forms.ModelForm):
    """Form for creating/editing signature workflows"""
    
    class Meta:
        model = ElectronicSignature
        fields = '__all__'


class StampArtifactUploadForm(forms.Form):
    """Form to upload an encrypted stamp artifact (any file format)."""
    file = forms.FileField(
        required=True,
        label='Stamp file',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )
    device_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput()
    )

