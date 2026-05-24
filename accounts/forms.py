from django import forms
from django.contrib.auth.models import User

from .constants import ROLE_PROFESOR
from .models import UserProfile


class AcademicStudentRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        label='Nombre',
    )
    last_name = forms.CharField(
        max_length=150,
        label='Apellido',
    )
    email = forms.EmailField(
        label='Correo electronico',
    )
    username = forms.CharField(
        max_length=150,
        label='Nombre de usuario',
        help_text='Identificador con el que el estudiante iniciara sesion.',
    )
    student_code = forms.CharField(
        max_length=50,
        label='Codigo estudiantil',
    )
    max_cases = forms.IntegerField(
        min_value=1,
        label='Carga academica maxima',
        initial=5,
    )
    availability = forms.BooleanField(
        required=False,
        initial=True,
        label='Disponible para asignacion',
    )
    preferred_room = forms.ChoiceField(
        choices=UserProfile.ROOM_CHOICES,
        label='Sala preferente',
    )
    supervising_professor = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label='Profesor supervisor',
        empty_label='Sin profesor asignado',
    )
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Contrasena inicial',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supervising_professor'].queryset = (
            User.objects.filter(
                is_active=True,
                groups__name=ROLE_PROFESOR,
            )
            .distinct()
            .order_by('first_name', 'last_name', 'username')
        )
        for field_name, field in self.fields.items():
            if field_name == 'availability':
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Ya existe un usuario con este nombre.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario con este correo.')
        return email

    def clean_student_code(self):
        student_code = self.cleaned_data['student_code'].strip()
        if UserProfile.objects.filter(student_code=student_code).exists():
            raise forms.ValidationError('Ya existe un estudiante con este codigo.')
        return student_code
