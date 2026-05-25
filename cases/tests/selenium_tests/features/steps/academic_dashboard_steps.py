import os

from behave import given, when, then

from pages.academic_dashboard_page import AcademicDashboardPage
from pages.do_login_page import LoginPage


def _get_credentials():
    return {
        'user': os.getenv('ACADEMIC_DASHBOARD_USER', 'profesor1'),
        'password': os.getenv('ACADEMIC_DASHBOARD_PASSWORD', 'Prof1234!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
    }


@given('existen estudiantes registrados en el sistema')
def step_given_students_exist(context):
    context.credentials = _get_credentials()


@given('el profesor accede al sistema')
def step_given_professor_login(context):
    context.credentials = _get_credentials()
    context.do_login_page = LoginPage(context.driver)
    context.dashboard_page = AcademicDashboardPage(context.driver)

    context.do_login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.do_login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )


@when('abre el panel de control academico')
def step_when_open_dashboard(context):
    context.dashboard_page.go_to_panel(context.credentials['base_url'])
    context.dashboard_page.wait_for_panel()


@then('el sistema muestra metricas y progreso de los estudiantes')
def step_then_dashboard_metrics(context):
    context.dashboard_page.metrics_visible()
    has_students = context.dashboard_page.has_students()
    assert has_students, 'No hay estudiantes visibles en el panel academico.'


@given('el profesor selecciona un estudiante')
def step_given_select_student(context):
    context.credentials = _get_credentials()
    context.do_login_page = LoginPage(context.driver)
    context.dashboard_page = AcademicDashboardPage(context.driver)

    context.do_login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.do_login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )
    context.dashboard_page.go_to_panel(context.credentials['base_url'])
    context.dashboard_page.wait_for_panel()

    opened = context.dashboard_page.open_first_student_detail()
    assert opened, 'No se encontro un estudiante para abrir el detalle.'


@when('consulta su informacion')
def step_when_view_student(context):
    context.dashboard_page.wait_for_student_detail()


@then('el sistema muestra su desempeno y casos asignados')
def step_then_student_detail(context):
    context.dashboard_page.student_metrics_visible()
    has_cases = context.dashboard_page.student_cases_visible()
    assert has_cases, 'El estudiante no tiene casos asignados en la vista.'
