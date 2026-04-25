from django import forms

from .models import Cite


class CiteForm(forms.ModelForm):
    class Meta:
        model = Cite
        fields = ['modality_cite', 'request_cite', 'date_assigned','description']
        widgets = {
            'modality_cite': forms.Select(attrs={
                'class': 'form-select'
            }),
            'request_cite': forms.Select(attrs={'class': 'form-select'}),
            'date_assigned': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe brevemente el motivo de la cita',
            }),
        }
        labels = {
            'modality_cite': 'Modalidad de Atención',
            'request_cite': 'Canal de solicitud',
            'description': 'Descripcion de la consulta',
            'date_assigned': 'Asignar fecha'
        }

    def clean_modality_cite(self):
        modality = self.cleaned_data.get('modality_cite')
        if not modality:
            raise forms.ValidationError('Selecciona una modalidad de atencion.')
        return modality
