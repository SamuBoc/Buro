import os

from behave import given, when, then

from pages.case_reassignment_page import CaseReassignmentPage
from pages.do_login_page import LoginPage


def _get_credentials():
    return {
        'user': os.getenv('CASE_REASSIGN_USER', 'profesor1'),
        'password': os.getenv('CASE_REASSIGN_PASSWORD', 'Prof1234!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
        'case_id': os.getenv('CASE_REASSIGN_CASE_ID', '').strip(),
    }


def _get_no_permission_credentials():
    fallback_case_id = os.getenv('CASE_REASSIGN_CASE_ID', '').strip()
    return {
        'user': os.getenv('CASE_REASSIGN_NO_PERMISSION_USER', 'estudiante1'),
        'password': os.getenv('CASE_REASSIGN_NO_PERMISSION_PASSWORD', 'Estu1234!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
        'case_id': os.getenv('CASE_REASSIGN_NO_PERMISSION_CASE_ID', '').strip() or fallback_case_id,
    }


@given('existe un caso asignado a un estudiante')
def step_given_case_exists(context):
    context.credentials = _get_credentials()


@given('la secretaria accede al detalle del caso')
def step_given_secretary_open_case(context):
    context.credentials = _get_credentials()
    context.do_login_page = LoginPage(context.driver)
    context.case_page = CaseReassignmentPage(context.driver)

    context.do_login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.do_login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )

    context.case_page.go_to_case_list(context.credentials['base_url'])
    opened = context.case_page.open_first_case_detail()
    if not opened and context.credentials['case_id']:
        context.case_page.go_to_case_detail(
            context.credentials['base_url'],
            context.credentials['case_id'],
        )
        opened = True
    assert opened, 'No se encontro un caso para abrir el detalle.'
    context.case_page.wait_for_detail()
    context.case_id = context.case_page.get_case_id_from_url()


@when('selecciona un nuevo estudiante')
def step_when_select_new_student(context):
    selected = context.case_page.select_different_student()
    assert selected, 'No hay un estudiante alterno disponible para reasignar.'
    context.new_student_name = selected


@when('confirma la reasignacion')
def step_when_confirm_reassign(context):
    context.case_page.submit_reassign()
    context.case_page.wait_for_detail()


@then('el sistema actualiza el estudiante responsable del caso')
def step_then_assigned_student_updated(context):
    assigned_text = context.case_page.assigned_student_text()
    assert context.new_student_name in assigned_text, (
        'El estudiante asignado no se actualizo en el detalle del caso.'
    )


@then('registra la accion en la bitacora')
def step_then_log_registered(context):
    has_entries = context.case_page.log_has_entries()
    assert has_entries, 'No hay registros en la bitacora de reasignaciones.'
    assert context.case_page.log_contains_text(context.new_student_name), (
        'La bitacora no incluye el nuevo estudiante reasignado.'
    )


@given('un usuario sin permisos intenta reasignar un caso')
def step_given_user_no_permission(context):
    context.credentials = _get_no_permission_credentials()
    context.do_login_page = LoginPage(context.driver)
    context.case_page = CaseReassignmentPage(context.driver)

    context.do_login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.do_login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )

    if context.credentials['case_id']:
        context.case_id = context.credentials['case_id']
        return

    context.case_page.go_to_case_list(context.credentials['base_url'])
    case_url = context.case_page.get_first_case_detail_url()
    if not case_url and context.credentials['case_id']:
        context.case_id = context.credentials['case_id']
        return
    assert case_url, 'No se encontro un caso para intentar la reasignacion.'
    context.case_id = case_url.rstrip('/').split('/')[-1]


@when('intenta realizar la reasignacion')
def step_when_attempt_reassign(context):
    context.case_page.go_to_reassign(context.credentials['base_url'], context.case_id)


@then('el sistema bloquea la accion')
def step_then_blocked(context):
    context.case_page.no_permission_visible()


@then('muestra un mensaje indicando que no tiene permisos')
def step_then_no_permission_message(context):
    context.case_page.no_permission_message_visible()
