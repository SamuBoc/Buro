import os
import sqlite3
import sys
from datetime import date

from behave import given, when, then

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pages.do_login_page import LoginPage


def _get_credentials():
    return {
        'user': os.getenv('CITE_HU18_USER', 'secretaria1'),
        'password': os.getenv('CITE_HU18_PASSWORD', 'Cambiar123!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
    }


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))


def _db_path():
    return os.path.join(_repo_root(), 'db.sqlite3')


def _ensure_test_data():
    beneficiary_id = 'BEN-HU18-0001'
    cite_id = 900018
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
                'Beneficiario HU18',
                beneficiary_id,
                'Cali',
                'hu18_beneficiary@test.com',
                today,
                '123456789',
                '3001234567',
            ),
        )

        connection.execute(
            '''
            INSERT INTO cite_cite (
                id, date_assigned, modality_cite, state_cite, request_cite,
                description, beneficiary_id, reminder_sent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                date_assigned = excluded.date_assigned,
                modality_cite = excluded.modality_cite,
                state_cite = excluded.state_cite,
                request_cite = excluded.request_cite,
                description = excluded.description,
                beneficiary_id = excluded.beneficiary_id,
                reminder_sent = excluded.reminder_sent
            ''',
            (
                cite_id,
                today,
                'PRESENCIAL',
                'Pendiente',
                'Página Web',
                'Cita HU18 automatizada',
                beneficiary_id,
                0,
            ),
        )
        connection.commit()

    return beneficiary_id, cite_id


def _set_cite_state(cite_id, state):
    with sqlite3.connect(_db_path()) as connection:
        connection.execute(
            'UPDATE cite_cite SET state_cite = ? WHERE id = ?',
            (state, cite_id),
        )
        connection.commit()


def _get_cite_state(cite_id):
    with sqlite3.connect(_db_path()) as connection:
        row = connection.execute(
            'SELECT state_cite FROM cite_cite WHERE id = ?',
            (cite_id,),
        ).fetchone()

    return row[0] if row else None


@given('existe una cita programada')
def step_given_cite_programmed(context):
    context.credentials = _get_credentials()
    context.beneficiary_id, context.cite_id = _ensure_test_data()


@given('la secretaria inicia sesion en el sistema')
def step_given_secretary_logs_in(context):
    context.login_page = LoginPage(context.driver)
    context.login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )


@given('el beneficiario asiste a la cita')
def step_given_beneficiary_attends(context):
    context.expected_state = 'Asistió'


@given('el beneficiario no se presenta a la cita')
def step_given_beneficiary_does_not_show(context):
    context.expected_state = 'No asistió'


@when('la secretaria registra la asistencia')
def step_when_register_attendance(context):
    _set_cite_state(context.cite_id, 'Asistió')


@when('la secretaria registra la inasistencia')
def step_when_register_no_show(context):
    _set_cite_state(context.cite_id, 'No asistió')


@then('el sistema actualiza el estado de la cita a "Asistió"')
def step_then_state_attended(context):
    assert _get_cite_state(context.cite_id) == 'Asistió', (
        'El sistema no actualizo la cita a estado Asistio.'
    )


@then('el sistema actualiza el estado de la cita a "No asistió"')
def step_then_state_no_show(context):
    assert _get_cite_state(context.cite_id) == 'No asistió', (
        'El sistema no actualizo la cita a estado No asistio.'
    )
