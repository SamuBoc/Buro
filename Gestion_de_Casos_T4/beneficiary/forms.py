from django import forms
from .models import Beneficiary


class BeneficiaryForm(forms.ModelForm):

    allow_conditions = forms.BooleanField(required=True)

    class Meta:
        model = Beneficiary
        fields = ['name', 'location', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo',
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
            'name':     'Nombre',
            'location': 'Ubicación',
            'phone':    'Teléfono',
            'email':    'Correo electrónico',
        }


class Update_Beneficiary_Form(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = ['name', 'location', 'phone', 'email']  # ← id eliminado
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo',
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
            'name':     'Nombre',
            'location': 'Ubicación',
            'phone':    'Teléfono',
            'email':    'Correo electrónico',
        }