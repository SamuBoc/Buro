"""
Precondición: environment.py crea automáticamente los usuarios y datos de prueba
antes de correr los escenarios. No se necesita setup manual en la DB.
"""
from behave import given, when, then
from selenium.webdriver.common.by import By
from pages.login_page import LoginPage
from pages.recording_access_page import RecordingAccessPage

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
    case_id = getattr(context, 'selenium_case_id', None)
    assert case_id is not None, \
        "No hay caso con grabación en la DB. Suba una grabación primero."
    context.recording_page.go_to_case(case_id)


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
    interaction_id = getattr(context, 'selenium_interaction_id', None)
    assert interaction_id is not None, \
        "No hay interacción con grabación en la DB."
    context.recording_page.go_to_recording(interaction_id)


@then('La secretaria es redirigida o recibe acceso denegado a la grabacion')
def step_access_denied(context):
    url = context.recording_page.get_current_url()
    body_text = context.driver.find_element(By.TAG_NAME, 'body').text
    body_lower = body_text.lower()
    is_blocked = (
        'login' in url
        or 'sin-permisos' in url
        or '403' in body_text
        or 'forbidden' in body_lower
        or 'denegado' in body_lower
        or 'permiso' in body_lower
    )
    assert is_blocked, \
        f"Se esperaba redirect al login o respuesta 403. URL actual: {url}"
