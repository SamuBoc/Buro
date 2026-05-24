from datetime import date

from django import forms

from .models import Cite


class CiteForm(forms.ModelForm):
    modality_cite = forms.ChoiceField(
        choices=[('', 'Seleccione una modalidad')] + list(Cite.MODALITY_CHOICES),
        required=True,
        label='Modalidad',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Cite
        fields = ['modality_cite', 'request_cite', 'date_assigned', 'description']
        widgets = {
            'request_cite':  forms.Select(attrs={'class': 'form-select'}),
            'date_assigned': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'modality_cite': 'Modalidad',
            'request_cite':  'Medio de Solicitud',
            'date_assigned': 'Fecha de Asignación',
            'description':   'Descripcion',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_assigned'].required = False

    def clean_date_assigned(self):
        value = self.cleaned_data.get('date_assigned')
        return value or date.today()

    def clean_modality_cite(self):
        modality = self.cleaned_data.get('modality_cite')
        if not modality:
            raise forms.ValidationError('Debes seleccionar una modalidad valida para continuar.')
        return modality


class RescheduleCiteForm(forms.ModelForm):
    class Meta:
        model = Cite
        fields = ['date_assigned']
        widgets = {
            'date_assigned': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'date_assigned': 'Fecha de Asignación',
        }