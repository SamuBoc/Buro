import os
import sys
from datetime import date

from behave import given, when, then
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django

django.setup()

from django.contrib.auth.models import Group, User

from accounts.constants import ROLE_SECRETARIA
from beneficiary.models import Beneficiary
from cite.models import Cite

from pages.do_login_page import LoginPage
from pages.hu18_attendance_page import HU18AttendancePage


def _get_credentials():
    return {
        'user': os.getenv('CITE_HU18_USER', 'secretaria1'),
        'password': os.getenv('CITE_HU18_PASSWORD', 'Cambiar123!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
    }


def _ensure_secretary_user(username, password):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': f'{username}@test.com'},
    )
    if created or not user.check_password(password):
        user.set_password(password)
        user.save()

    group, _ = Group.objects.get_or_create(name=ROLE_SECRETARIA)
    user.groups.add(group)
    return user


def _ensure_test_data():
    beneficiary_id = 'BEN-HU18-0001'
    cite_id = 900018
    today = date.today()

    beneficiary, _ = Beneficiary.objects.update_or_create(
        id=beneficiary_id,
        defaults={
            'name': 'Beneficiario HU18',
            'location': 'Cali',
            'email': 'hu18_beneficiary@test.com',
            'colombian_identification': '123456789',
            'phone': '3001234567',
        },
    )

    Cite.objects.update_or_create(
        id=cite_id,
        defaults={
            'date_assigned': today,
            'modality_cite': Cite.MODALITY_INPERSON,
            'state_cite': Cite.STATE_PENDING,
            'request_cite': Cite.CHANNEL_WEB,
            'description': 'Cita HU18 automatizada',
            'beneficiary': beneficiary,
            'reminder_sent': False,
        },
    )

    return beneficiary_id, cite_id


def _normalize_status_label(label):
    return label.strip().lower()


@given('existe una cita programada')
def step_given_cite_programmed(context):
    context.credentials = _get_credentials()
    _ensure_secretary_user(
        context.credentials['user'],
        context.credentials['password'],
    )
    context.beneficiary_id, context.cite_id = _ensure_test_data()


@given('la secretaria inicia sesion en el sistema')
def step_given_secretary_logs_in(context):
    context.login_page = LoginPage(context.driver)
    context.attendance_page = HU18AttendancePage(context.driver)
    context.login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )
    WebDriverWait(context.driver, 10).until(
        lambda driver: '/login/' not in driver.current_url
    )


@given('el beneficiario asiste a la cita')
def step_given_beneficiary_attends(context):
    context.expected_state = 'Asistió'
    context.attendance_status = 'asistio'


@given('el beneficiario no se presenta a la cita')
def step_given_beneficiary_does_not_show(context):
    context.expected_state = 'No asistió'
    context.attendance_status = 'no-asistio'


@when('la secretaria registra la asistencia')
def step_when_register_attendance(context):
    context.attendance_page.go_to_beneficiary_cites(
        context.credentials['base_url'],
        context.beneficiary_id,
    )
    context.attendance_page.wait_for_cite_list()
    context.attendance_page.register_attendance(
        context.cite_id,
        context.attendance_status,
    )


@when('la secretaria registra la inasistencia')
def step_when_register_no_show(context):
    context.attendance_page.go_to_beneficiary_cites(
        context.credentials['base_url'],
        context.beneficiary_id,
    )
    context.attendance_page.wait_for_cite_list()
    context.attendance_page.register_attendance(
        context.cite_id,
        context.attendance_status,
    )


@then('el sistema actualiza el estado de la cita a "Asistió"')
def step_then_state_attended(context):
    context.attendance_page.wait_for_state(
        context.cite_id,
        context.expected_state,
    )
    assert (
        _normalize_status_label(context.attendance_page.state_text(context.cite_id))
        == _normalize_status_label(context.expected_state)
    ), 'El sistema no actualizo la cita a estado Asistio.'


@then('el sistema actualiza el estado de la cita a "No asistió"')
def step_then_state_no_show(context):
    context.attendance_page.wait_for_state(
        context.cite_id,
        context.expected_state,
    )
    assert (
        _normalize_status_label(context.attendance_page.state_text(context.cite_id))
        == _normalize_status_label(context.expected_state)
    ), 'El sistema no actualizo la cita a estado No asistio.'
