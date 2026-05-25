from datetime import date

from django import forms
from django.utils import timezone

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
        return value or timezone.localdate()


class RescheduleCiteForm(forms.ModelForm):
    date_assigned = forms.DateTimeField(
        label='Fecha de Asignación',
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'class': 'form-control', 'type': 'datetime-local'}
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = Cite
        fields = ['date_assigned']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.pk and instance.date_assigned:
            dt = instance.date_assigned
            if timezone.is_aware(dt):
                dt = dt.replace(tzinfo=None)
            self.initial['date_assigned'] = dt
