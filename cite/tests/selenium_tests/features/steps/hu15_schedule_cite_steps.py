import os
from datetime import date

from behave import given, when, then

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django

django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from beneficiary.models import Beneficiary
from cite.models import Cite
from pages.do_login_page import LoginPage
from pages.hu15_schedule_cite_page import HU15ScheduleCitePage


def _get_credentials():
    return {
        'user': os.getenv('CITE_HU15_USER', 'secretaria1'),
        'password': os.getenv('CITE_HU15_PASSWORD', 'Cambiar123!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
    }


def _ensure_test_user(username, password):
    user, _ = User.objects.get_or_create(username=username, defaults={'email': f'{username}@test.com'})
    user.email = f'{username}@test.com'
    user.set_password(password)
    user.save()
    secretaria_group, _ = Group.objects.get_or_create(name='secretaria')
    user.groups.add(secretaria_group)
    return user


def _ensure_test_beneficiary():
    beneficiary, _ = Beneficiary.objects.get_or_create(
        email='hu15_beneficiary@test.com',
        defaults={
            'name': 'Beneficiario HU15',
            'location': 'Cali',
            'phone': '3001234567',
        },
    )
    beneficiary.name = 'Beneficiario HU15'
    beneficiary.location = 'Cali'
    beneficiary.phone = '3001234567'
    beneficiary.save()
    return beneficiary


@given('existe un beneficiario disponible para agendar cita')
def step_given_beneficiary_available(context):
    context.credentials = _get_credentials()
    _ensure_test_user(context.credentials['user'], context.credentials['password'])
    beneficiary = _ensure_test_beneficiary()
    context.beneficiary_id = beneficiary.id
    context.beneficiary_name = beneficiary.name


@given('la secretaria accede al formulario de agendamiento de cita')
def step_given_secretary_opens_form(context):
    context.login_page = LoginPage(context.driver)
    context.cite_page = HU15ScheduleCitePage(context.driver)

    context.login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.login_page.make_log_in(context.credentials['user'], context.credentials['password'])
    context.cite_page.go_to_beneficiary_detail(context.credentials['base_url'], context.beneficiary_id)
    try:
        context.cite_page.open_cite_form_from_detail()
    except Exception:
        context.cite_page.go_to_cite_form(context.credentials['base_url'], context.beneficiary_id)
    context.cite_page.wait_for_cite_form()


@when('selecciona la modalidad telefonica')
def step_when_select_phone_modality(context):
    context.cite_page.select_modality('TELEFONICA')


@when('intenta agendar sin seleccionar modalidad')
def step_when_leave_modality_blank(context):
    pass


@when('completa la fecha y la descripcion de la cita')
def step_when_fill_date_and_description(context):
    context.cite_date = date.today().isoformat()
    context.cite_description = 'Consulta juridica para validar el canal de atencion.'
    context.cite_page.fill_date(context.cite_date)
    context.cite_page.fill_description(context.cite_description)


@when('registra la cita')
def step_when_submit_cite(context):
    context.cite_page.submit()


@then('el sistema guarda la cita con la modalidad seleccionada')
def step_then_cite_saved_with_modality(context):
    context.cite_page.wait_for_cite_saved(
        context.beneficiary_id,
        'TELEFONICA',
        context.cite_description,
    )


@then('el sistema solicita seleccionar una modalidad valida')
def step_then_modality_validation(context):
    assert context.cite_page.error_visible(), 'No se mostro el mensaje de validacion de modalidad.'
