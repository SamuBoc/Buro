from behave import given, then, when

from pages.case_access_page import CaseAccessPage
from pages.login_page import LoginPage


@given("existe un caso registrado en el sistema")
def step_case_exists(context):
    case_id = getattr(context, "selenium_hu12_case_id", None)
    assert case_id is not None, "No se preparo el caso Selenium para HU-12."
    context.case_access_page = CaseAccessPage(context.driver)


@given("el estudiante asignado intenta acceder al caso")
def step_assigned_student_login(context):
    context.login_page = LoginPage(context.driver)
    context.case_access_page = CaseAccessPage(context.driver)
    context.login_page.login(
        context.selenium_assigned_student_username,
        context.selenium_assigned_student_password,
    )


@when("abre el detalle del caso")
def step_open_case_detail(context):
    context.case_access_page.go_to_case_detail(context.selenium_hu12_case_id)


@then("el sistema muestra toda la informacion del expediente")
def step_case_detail_visible(context):
    page_text = context.case_access_page.get_page_text()
    assert context.case_access_page.current_url_is_case_detail(context.selenium_hu12_case_id), (
        f"Se esperaba estar en el detalle del caso, URL actual: {context.driver.current_url}"
    )
    assert "Detalle del Caso" in page_text, "No se mostro el encabezado del detalle del caso."
    assert "Descripcion del problema" in page_text, "No se mostro la descripcion del expediente."
    assert "Estudiante asignado" in page_text, "No se mostro la informacion del estudiante asignado."


@given("un usuario no autorizado intenta acceder al caso")
def step_unassigned_student_login(context):
    context.login_page = LoginPage(context.driver)
    context.case_access_page = CaseAccessPage(context.driver)
    context.login_page.login(
        context.selenium_unassigned_student_username,
        context.selenium_unassigned_student_password,
    )


@when("intenta abrir el detalle completo")
def step_unassigned_opens_case_detail(context):
    context.case_access_page.go_to_case_detail(context.selenium_hu12_case_id)


@then("el sistema bloquea el acceso")
def step_access_is_blocked(context):
    assert not context.case_access_page.current_url_is_case_detail(context.selenium_hu12_case_id), (
        "El usuario no autorizado no deberia permanecer en el detalle del caso."
    )
    assert context.case_access_page.is_in_case_list(), (
        f"Se esperaba redireccion al listado de casos, URL actual: {context.driver.current_url}"
    )


@then("muestra un mensaje indicando que no tiene permisos")
def step_permission_message(context):
    assert context.case_access_page.has_permission_alert(), (
        "No se encontro el mensaje de acceso denegado esperado."
    )
