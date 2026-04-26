from django import forms
from .models import Beneficiary, DocumentBeneficiary


class BeneficiaryForm(forms.ModelForm):

    allow_conditions = forms.BooleanField(required=True)

    class Meta:
        model = Beneficiary
        fields = ['name', 'colombian_identification', 'location', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo',
            }),
            'colombian_identification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Identificación',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad, Departamento',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 3001234567',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
            }),
        }
        labels = {
            'name':                    'Nombre',
            'colombian_identification': 'Identificación',
            'location':                'Ubicación',
            'phone':                   'Teléfono',
            'email':                   'Correo electrónico',
        }


class DocumentBeneficiaryForm(forms.ModelForm):
    class Meta:
        model = DocumentBeneficiary
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.png,.jpg,.jpeg',
            }),
        }
        labels = {
            'file': 'Documento de identidad',
        }


class Update_Beneficiary_Form(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = ['name', 'colombian_identification', 'location', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo',
            }),
            'colombian_identification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Identificación',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ciudad, Departamento',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 3001234567',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
            }),
        }
        labels = {
            'name':                    'Nombre',
            'colombian_identification': 'Identificación',
            'location':                'Ubicación',
            'phone':                   'Teléfono',
            'email':                   'Correo electrónico',
        }
