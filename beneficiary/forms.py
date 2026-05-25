import os

from django import forms

from .models import Beneficiary, DataDeletionRequest, DocumentBeneficiary


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
                'placeholder': 'Identificacion',
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
            'colombian_identification': 'Identificacion',
            'location':                'Ubicacion',
            'phone':                   'Telefono',
            'email':                   'Correo electronico',
        }


class DocumentBeneficiaryForm(forms.ModelForm):

    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}

    ALLOWED_CONTENT_TYPES = {
        'application/pdf',
        'image/png',
        'image/jpeg',
    }

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

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise forms.ValidationError(
                    'Formato no permitido. Solo se aceptan archivos PDF, PNG, JPG o JPEG.'
                )

            content_type = getattr(file, 'content_type', None)
            if content_type and content_type not in self.ALLOWED_CONTENT_TYPES:
                raise forms.ValidationError(
                    'El contenido del archivo no corresponde a un formato permitido '
                    '(PDF, PNG o JPEG).'
                )

        return file


class UpdateBeneficiaryForm(forms.ModelForm):
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
                'placeholder': 'Identificacion',
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
            'colombian_identification': 'Identificacion',
            'location':                'Ubicacion',
            'phone':                   'Telefono',
            'email':                   'Correo electronico',
        }


class DataDeletionRequestForm(forms.ModelForm):
    confirm_request = forms.BooleanField(
        required=True,
        label='Confirmo que deseo solicitar la eliminacion de mis datos personales.',
    )

    class Meta:
        model = DataDeletionRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Motivo de la solicitud (opcional).',
            }),
        }
        labels = {
            'reason': 'Motivo de la solicitud',
        }