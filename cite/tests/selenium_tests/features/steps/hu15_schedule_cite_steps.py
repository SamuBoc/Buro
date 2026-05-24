import os
import sqlite3
import sys
from datetime import date

from behave import given, when, then

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pages.do_login_page import LoginPage
from pages.hu15_schedule_cite_page import HU15ScheduleCitePage


def _get_credentials():
    return {
        'user': os.getenv('CITE_HU15_USER', 'secretaria1'),
        'password': os.getenv('CITE_HU15_PASSWORD', 'Cambiar123!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
    }


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))


def _db_path():
    return os.path.join(_repo_root(), 'db.sqlite3')


def _ensure_test_beneficiary():
    beneficiary_id = 'BEN-HU15-0001'
    today = date.today().isoformat()

    with sqlite3.connect(_db_path()) as connection:
        connection.execute(
            '''
            INSERT INTO beneficiary_beneficiary (
                name, id, location, email, date_register, colombian_identification, phone
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                location = excluded.location,
                email = excluded.email,
                date_register = excluded.date_register,
                colombian_identification = excluded.colombian_identification,
                phone = excluded.phone
            ''',
            (
                'Beneficiario HU15',
                beneficiary_id,
                'Cali',
                'hu15_beneficiary@test.com',
                today,
                '123456789',
                '3001234567',
            ),
        )
        connection.commit()

    return beneficiary_id


@given('existe un beneficiario disponible para agendar cita')
def step_given_beneficiary_available(context):
    context.credentials = _get_credentials()
    context.beneficiary_id = _ensure_test_beneficiary()
    context.beneficiary_name = 'Beneficiario HU15'


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
