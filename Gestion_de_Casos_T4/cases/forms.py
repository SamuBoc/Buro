from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Case


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput(attrs={'class': 'form-control'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]

        return [single_file_clean(data, initial)]


class CaseForm(forms.ModelForm):
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.docx', '.xlsx'}

    documents = MultipleFileField(
        label='Documentos del caso',
        required=True
    )

    class Meta:
        model = Case
        fields = ['sala', 'description', 'beneficiary', 'assigned_student', 'deadline_date']
        widgets = {
            'sala': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describa el problema juridico presentado por el beneficiario.',
            }),
            'beneficiary': forms.Select(attrs={'class': 'form-select'}),
            'assigned_student': forms.Select(attrs={'class': 'form-select'}),
            'deadline_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'sala': 'Sala juridica',
            'description': 'Descripcion del problema',
            'beneficiary': 'Beneficiario asociado',
            'assigned_student': 'Estudiante asignado',
            'deadline_date': 'Fecha limite de atencion',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['beneficiary'].empty_label = 'Seleccione un beneficiario'
        self.fields['beneficiary'].queryset = self.fields['beneficiary'].queryset.order_by('name')
        self.fields['assigned_student'].required = False
        self.fields['assigned_student'].empty_label = 'Seleccione un estudiante'
        self.fields['assigned_student'].queryset = User.objects.filter(
            groups__name='estudiante'
        ).order_by('first_name', 'last_name', 'username').distinct()
        self.fields['documents'].widget.attrs.update({
            'accept': '.pdf,.jpg,.jpeg,.png,.docx,.xlsx'
        })

    def clean_documents(self):
        documents = self.cleaned_data.get('documents') or self.files.getlist('documents')

        if not isinstance(documents, (list, tuple)):
            documents = [documents]

        if not documents:
            raise ValidationError('Debe cargar al menos un documento para el caso.')

        invalid_files = []
        for document in documents:
            extension = f".{document.name.split('.')[-1].lower()}" if '.' in document.name else ''
            if extension not in self.ALLOWED_EXTENSIONS:
                invalid_files.append(document.name)

        if invalid_files:
            raise ValidationError(
                'Los siguientes archivos no son validos: '
                + ', '.join(invalid_files)
                + '. Formatos permitidos: PDF, JPG, PNG, DOCX, XLSX.'
            )

        return documents


class CaseDeadlineForm(forms.ModelForm):
    class Meta:
        model = Case
        fields = ['deadline_date']
        widgets = {
            'deadline_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'deadline_date': 'Fecha limite de atencion',
        }


class CaseReassignmentForm(forms.Form):
    assigned_student = forms.ModelChoiceField(
        label='Nuevo estudiante',
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        self.case = kwargs.pop('case', None)
        super().__init__(*args, **kwargs)
        self.fields['assigned_student'].queryset = User.objects.filter(
            is_active=True,
            groups__name='estudiante'
        ).order_by('first_name', 'last_name', 'username').distinct()

        if self.case and self.case.assigned_student_id:
            self.initial.setdefault('assigned_student', self.case.assigned_student_id)

    def clean_assigned_student(self):
        assigned_student = self.cleaned_data['assigned_student']

        if self.case and assigned_student.id == self.case.assigned_student_id:
            raise ValidationError('El caso ya esta asignado a ese estudiante.')

        return assigned_student
