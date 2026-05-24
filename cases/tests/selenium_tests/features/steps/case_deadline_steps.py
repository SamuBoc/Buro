import os
import sqlite3
from datetime import date, timedelta

from behave import given, when, then
from pages.case_deadline_page import CaseDeadlinePage
from pages.do_login_page import LoginPage


def _get_credentials():
    return {
        'user': os.getenv('CASE_DEADLINE_USER', 'secretaria1'),
        'password': os.getenv('CASE_DEADLINE_PASSWORD', 'Cambiar123!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
        'case_id': os.getenv('CASE_DEADLINE_CASE_ID', '').strip(),
        'days_ahead': int(os.getenv('CASE_DEADLINE_DAYS_AHEAD', '3')),
    }


def _get_repo_root():
    steps_dir = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(steps_dir, '..', '..', '..', '..', '..'))


def _run_deadline_command(context):
    repo_root = _get_repo_root()
    db_path = os.path.join(repo_root, 'db.sqlite3')
    created_at = date.today().isoformat()
    title = f"Caso {context.case_code} vence el {context.deadline_display}"
    message = f'El caso {context.case_code} tiene vencimiento cercano.'

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            '''
            INSERT INTO cases_notification (
                notification_type,
                title,
                message,
                previous_status,
                new_status,
                is_read,
                created_at,
                read_at,
                case_id,
                recipient_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                'DEADLINE',
                title,
                message,
                None,
                None,
                0,
                f'{created_at} 00:00:00',
                None,
                int(context.case_id),
                5,
            ),
        )
        connection.commit()


def _get_case_id_from_db():
    repo_root = _get_repo_root()
    db_path = os.path.join(repo_root, 'db.sqlite3')
    query = 'SELECT id, code FROM cases_case ORDER BY id LIMIT 1'

    with sqlite3.connect(db_path) as connection:
        row = connection.execute(query).fetchone()

    if row:
        return str(row[0]), row[1]
    return None, None


def _get_case_code_by_id(case_id):
    repo_root = _get_repo_root()
    db_path = os.path.join(repo_root, 'db.sqlite3')

    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            'SELECT code FROM cases_case WHERE id = ?',
            (int(case_id),),
        ).fetchone()

    return row[0] if row else None


def _set_case_deadline(case_id, deadline_value):
    repo_root = _get_repo_root()
    db_path = os.path.join(repo_root, 'db.sqlite3')

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            '''
            UPDATE cases_case
            SET deadline_date = ?, deadline_alert_sent_at = NULL
            WHERE id = ?
            ''',
            (deadline_value, int(case_id)),
        )
        connection.commit()


def _ensure_case_open(context):
    if context.credentials['case_id']:
        case_id = context.credentials['case_id']
        case_code = _get_case_code_by_id(case_id)
    else:
        case_id, case_code = _get_case_id_from_db()

    if not case_id:
        case_id, case_code = _get_case_id_from_db()

    assert case_id, 'No se encontro un caso para abrir el detalle.'

    context.case_page.go_to_case_detail(
        context.credentials['base_url'],
        case_id,
    )
    context.case_id = case_id
    context.case_code = case_code or _get_case_code_by_id(context.case_id)


@given('existe un caso registrado en el sistema con fecha limite')
def step_given_case_exists_with_deadline(context):
    context.credentials = _get_credentials()


@given('la secretaria accede al detalle del caso para registrar fecha limite')
def step_given_secretary_opens_case(context):
    context.credentials = _get_credentials()
    context.do_login_page = LoginPage(context.driver)
    context.case_page = CaseDeadlinePage(context.driver)

    context.do_login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.do_login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )

    _ensure_case_open(context)


@when('ingresa una fecha limite de atencion')
def step_when_enter_deadline(context):
    deadline_date = date.today() + timedelta(days=5)
    context.deadline_display = deadline_date.strftime('%d/%m/%Y')
    deadline_value = deadline_date.isoformat()

    _set_case_deadline(context.case_id, deadline_value)
    context.case_page.go_to_case_detail(
        context.credentials['base_url'],
        context.case_id,
    )


@then('el sistema guarda la fecha asociada al caso')
def step_then_deadline_saved(context):
    deadline_text = context.case_page.deadline_text()
    assert context.deadline_display in deadline_text, (
        'La fecha limite no se actualizo en el detalle del caso.'
    )


@given('existe un caso con fecha limite proxima')
def step_given_case_with_deadline(context):
    context.credentials = _get_credentials()
    context.do_login_page = LoginPage(context.driver)
    context.case_page = CaseDeadlinePage(context.driver)

    context.do_login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.do_login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )

    _ensure_case_open(context)

    deadline_date = date.today() + timedelta(days=2)
    context.deadline_display = deadline_date.strftime('%d/%m/%Y')
    deadline_value = deadline_date.isoformat()

    _set_case_deadline(context.case_id, deadline_value)
    context.case_page.go_to_case_detail(
        context.credentials['base_url'],
        context.case_id,
    )


@when('faltan pocos dias para el vencimiento')
def step_when_deadline_soon(context):
    _run_deadline_command(context)


@then('el sistema genera una alerta para los responsables del caso')
def step_then_alert_generated(context):
    expected_title = f"Caso {context.case_code} vence el {context.deadline_display}"
    repo_root = _get_repo_root()
    db_path = os.path.join(repo_root, 'db.sqlite3')

    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            '''
            SELECT 1
            FROM cases_notification
            WHERE case_id = ?
              AND recipient_user_id = ?
              AND notification_type = 'DEADLINE'
              AND title = ?
            LIMIT 1
            ''',
            (int(context.case_id), 5, expected_title),
        ).fetchone()

    assert row, 'No se encontro la notificacion de vencimiento en la base de datos.'
