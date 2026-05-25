import os
import sys
from datetime import date, timedelta

from behave import given, when, then
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django

django.setup()

from django.contrib.auth.models import Group, User

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_ESTUDIANTE, ROLE_PROFESOR, ROLE_SECRETARIA
from beneficiary.models import Beneficiary
from cases.models import Case
from cases.services import generate_deadline_alerts

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


def _ensure_user_with_role(username, password, role_name):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': f'{username}@test.com'},
    )
    if created or not user.check_password(password):
        user.set_password(password)
        user.save()

    group, _ = Group.objects.get_or_create(name=role_name)
    user.groups.add(group)
    return user


def _ensure_case(context):
    secretary = _ensure_user_with_role(
        context.credentials['user'],
        context.credentials['password'],
        ROLE_SECRETARIA,
    )
    _ensure_user_with_role('profesor_hu11', 'ClaveHu11!', ROLE_PROFESOR)
    _ensure_user_with_role('admin_hu11', 'ClaveHu11!', ROLE_ADMINISTRADOR)

    student = _ensure_user_with_role('estudiante_hu11', 'ClaveHu11!', ROLE_ESTUDIANTE)
    if not student.profile.student_code:
        student.profile.student_code = '20261101'
        student.profile.save()

    beneficiary, _ = Beneficiary.objects.update_or_create(
        id='BEN-HU11-0001',
        defaults={
            'name': 'Beneficiario HU11',
            'location': 'Cali',
            'email': 'hu11_beneficiary@test.com',
            'colombian_identification': '555666777',
            'phone': '3003344556',
        },
    )

    case, _ = Case.objects.update_or_create(
        description='Caso HU11 fecha limite',
        beneficiary=beneficiary,
        defaults={
            'sala': Case.ROOM_CIVIL,
            'assigned_student': student,
            'state': Case.STATE_ASSIGNED,
            'created_by': secretary,
        },
    )
    return case


@given('existe un caso registrado en el sistema con fecha limite')
def step_given_case_exists_with_deadline(context):
    context.credentials = _get_credentials()
    case = _ensure_case(context)
    context.case_id = case.pk
    context.case_code = case.code


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
    WebDriverWait(context.driver, 10).until(
        lambda driver: '/login/' not in driver.current_url
    )

    context.case_page.go_to_case_detail(
        context.credentials['base_url'],
        context.case_id,
    )
    context.case_page.wait_for_detail()


@when('ingresa una fecha limite de atencion')
def step_when_enter_deadline(context):
    deadline_date = date.today() + timedelta(days=5)
    context.deadline_display = deadline_date.strftime('%d/%m/%Y')
    deadline_value = deadline_date.isoformat()

    context.case_page.set_deadline(deadline_value)
    context.case_page.submit_deadline()
    context.case_page.wait_for_detail()


@then('el sistema guarda la fecha asociada al caso')
def step_then_deadline_saved(context):
    context.case_page.wait_for_deadline_text(context.deadline_display)
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
    WebDriverWait(context.driver, 10).until(
        lambda driver: '/login/' not in driver.current_url
    )

    case = _ensure_case(context)
    context.case_id = case.pk
    context.case_code = case.code

    deadline_date = date.today() + timedelta(days=2)
    context.deadline_display = deadline_date.strftime('%d/%m/%Y')
    deadline_value = deadline_date.isoformat()

    case.deadline_date = deadline_date
    case.deadline_alert_sent_at = None
    case.save(update_fields=['deadline_date', 'deadline_alert_sent_at'])

    context.case_page.go_to_case_detail(
        context.credentials['base_url'],
        context.case_id,
    )
    context.case_page.wait_for_detail()


@when('faltan pocos dias para el vencimiento')
def step_when_deadline_soon(context):
    generate_deadline_alerts(days_ahead=context.credentials['days_ahead'])


@then('el sistema genera una alerta para los responsables del caso')
def step_then_alert_generated(context):
    expected_title = f"Caso {context.case_code} vence el {context.deadline_display}"
    context.case_page.go_to_notifications(context.credentials['base_url'])
    context.case_page.wait_for_notifications()
    assert context.case_page.has_notification_title(expected_title), (
        'No se encontro la notificacion de vencimiento en el sistema.'
    )
