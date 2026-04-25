from django import forms

from .models import Cite


class CiteForm(forms.ModelForm):
    modality_cite = forms.ChoiceField(
        choices=[('', 'Seleccione una modalidad')] + list(Cite.MODALITY_CHOICES),
        required=True,
        label='Tipo de atencion',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Cite
        fields = ['modality_cite', 'request_cite', 'description']
        widgets = {
            'request_cite': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe brevemente el motivo de la cita',
            }),
        }
        labels = {
            'request_cite': 'Canal de solicitud',
            'description': 'Descripcion de la consulta',
        }

    def clean_modality_cite(self):
        modality = self.cleaned_data.get('modality_cite')
        if not modality:
            raise forms.ValidationError('Selecciona una modalidad de atencion.')
        return modality
