from datetime import date

from django import forms

from .models import Cite


class CiteForm(forms.ModelForm):
    class Meta:
        model = Cite
        fields = ['modality_cite', 'request_cite', 'date_assigned', 'description']
        widgets = {
            'modality_cite': forms.Select(attrs={'class': 'form-select'}),
            'request_cite':  forms.Select(attrs={'class': 'form-select'}),
            'date_assigned': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
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


class RescheduleCiteForm(forms.ModelForm):
    class Meta:
        model = Cite
        fields = ['date_assigned']
        widgets = {
            'date_assigned': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'date_assigned': 'Fecha de Asignación',
        }