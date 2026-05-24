import os

from behave import given, when, then

from pages.case_rejection_page import CaseRejectionPage
from pages.do_login_page import LoginPage


def _get_credentials():
    return {
        'user': os.getenv('CASE_REJECT_USER', 'secretaria1'),
        'password': os.getenv('CASE_REJECT_PASSWORD', 'Cambiar123!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
        'case_id': os.getenv('CASE_REJECT_CASE_ID', '').strip(),
        'reason': os.getenv(
            'CASE_REJECT_REASON',
            'No es posible asumir el caso por falta de competencia.'
        ),
    }


@given('existe un caso registrado en el sistema')
def step_given_case_exists(context):
    context.credentials = _get_credentials()


@given('la secretaria accede al caso')
def step_given_secretary_open_case(context):
    context.credentials = _get_credentials()
    context.do_login_page = LoginPage(context.driver)
    context.case_page = CaseRejectionPage(context.driver)

    context.do_login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.do_login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )

    opened = context.case_page.open_case_with_reject_form(
        context.credentials['base_url'],
        context.credentials['case_id'],
    )
    assert opened, (
        'No se encontro un caso disponible para rechazar. '
        'Verifica las credenciales o define CASE_REJECT_CASE_ID.'
    )
    context.case_page.wait_for_reject_form()
    context.case_id = context.case_page.get_case_id_from_url()


@when('selecciona la opcion "Rechazar caso"')
def step_when_select_reject_option(context):
    context.case_page.wait_for_reject_form()


@when('ingresa la causal de rechazo')
def step_when_enter_rejection_reason(context):
    context.rejection_reason = context.credentials['reason']
    context.case_page.enter_rejection_reason(context.rejection_reason)
    context.case_page.submit_reject()
    context.case_page.wait_for_detail()


@then('el sistema registra la causal')
def step_then_reason_registered(context):
    displayed_reason = context.case_page.rejection_reason_text()
    assert context.rejection_reason in displayed_reason, (
        'La causal de rechazo no se muestra en el detalle del caso.'
    )


@then('cambia el estado del caso a "Rechazado"')
def step_then_state_rejected(context):
    state_text = context.case_page.state_text()
    assert state_text == 'Rechazado', 'El estado del caso no cambio a Rechazado.'


@given('la secretaria intenta rechazar un caso')
def step_given_secretary_attempt_reject(context):
    step_given_secretary_open_case(context)


@when('no ingresa una causal de rechazo')
def step_when_empty_reason(context):
    context.case_page.enter_rejection_reason('   ')
    context.case_page.submit_reject()
    context.case_page.wait_for_detail()


@then('el sistema bloquea el rechazo')
def step_then_action_blocked(context):
    state_text = context.case_page.state_text()
    assert state_text != 'Rechazado', 'El caso fue rechazado sin causal valida.'


@then('solicita ingresar una causal valida')
def step_then_request_valid_reason(context):
    context.case_page.rejection_error_visible()
