"""
Precondición: debe existir en la DB local un caso con una interacción
de tipo llamada con audio_file subido.

Ajustar CASE_ID e INTERACTION_ID abajo según la DB de prueba.
"""
from behave import given, when, then
from pages.login_page import LoginPage
from pages.recording_access_page import RecordingAccessPage

CASE_ID = 1
INTERACTION_ID = 1

ADMIN_USER = "admin_selenium"
ADMIN_PASS = "selenium123"
SEC_USER = "secretaria_selenium"
SEC_PASS = "selenium123"


@given('El administrador inicia sesion')
def step_admin_login(context):
    context.login_page = LoginPage(context.driver)
    context.recording_page = RecordingAccessPage(context.driver)
    context.login_page.login(ADMIN_USER, ADMIN_PASS)


@given('La secretaria inicia sesion')
def step_secretaria_login(context):
    context.login_page = LoginPage(context.driver)
    context.recording_page = RecordingAccessPage(context.driver)
    context.login_page.login(SEC_USER, SEC_PASS)


@when('Ingresa al detalle del caso con grabacion')
def step_go_to_case(context):
    context.recording_page.go_to_case(CASE_ID)


@then('Ve el reproductor de audio en el historial de interacciones')
def step_audio_player_visible(context):
    assert context.recording_page.has_audio_player(), \
        "No se encontró el reproductor <audio controls> en la página"


@then('Ve el icono de candado en lugar del reproductor')
def step_lock_icon_visible(context):
    assert context.recording_page.has_lock_icon(), \
        "No se encontró el ícono de candado bi-lock-fill"
    assert not context.recording_page.has_audio_player(), \
        "La secretaria no debería ver el reproductor de audio"


@when('Intenta acceder a la URL de la grabacion directamente')
def step_direct_url_access(context):
    context.recording_page.go_to_recording(INTERACTION_ID)


@then('Es redirigida o recibe acceso denegado')
def step_access_denied(context):
    url = context.recording_page.get_current_url()
    body_text = context.recording_page.get_status_code_text()
    is_redirected = 'login' in url or '403' in body_text or 'Forbidden' in body_text or 'denegado' in body_text.lower()
    assert is_redirected, \
        f"Se esperaba redirect al login o 403. URL actual: {url}"
