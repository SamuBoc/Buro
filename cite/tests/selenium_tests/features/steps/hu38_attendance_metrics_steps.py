import os
import sys
from datetime import date, timedelta

from behave import given, when, then
from selenium.webdriver.support.ui import WebDriverWait

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django

django.setup()

from django.contrib.auth.models import Group, User

from accounts.constants import ROLE_ADMINISTRADOR
from beneficiary.models import Beneficiary
from cite.models import Cite

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pages.do_login_page import LoginPage
from pages.hu38_attendance_metrics_page import HU38AttendanceMetricsPage


def _get_credentials():
    return {
        'user': os.getenv('CITE_HU38_USER', 'admin'),
        'password': os.getenv('CITE_HU38_PASSWORD', 'Admin1234!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
    }


def _ensure_admin_user(username, password):
    user, created = User.objects.get_or_create(
        username=username,
        defaults={'email': f'{username}@test.com'},
    )
    if created or not user.check_password(password):
        user.set_password(password)
        user.save()

    group, _ = Group.objects.get_or_create(name=ROLE_ADMINISTRADOR)
    user.groups.add(group)
    return user


def _ensure_attendance_cites():
    beneficiary_id = 'BEN-HU38-0001'
    beneficiary, _ = Beneficiary.objects.update_or_create(
        id=beneficiary_id,
        defaults={
            'name': 'Beneficiario HU38',
            'location': 'Cali',
            'email': 'hu38_beneficiary@test.com',
            'colombian_identification': '987654321',
            'phone': '3007654321',
        },
    )

    cite_data = [
        (Cite.STATE_ATTENDED, -1, 'Cita HU38 asistida'),
        (Cite.STATE_NO_SHOW, -2, 'Cita HU38 no asistida'),
    ]

    for state, offset, description in cite_data:
        Cite.objects.update_or_create(
            beneficiary=beneficiary,
            description=description,
            defaults={
                'date_assigned': date.today() + timedelta(days=offset),
                'modality_cite': Cite.MODALITY_INPERSON,
                'state_cite': state,
                'request_cite': Cite.CHANNEL_WEB,
                'reminder_sent': False,
            },
        )


def _compute_expected_metrics():
    cites = Cite.objects.filter(state_cite__in=[Cite.STATE_ATTENDED, Cite.STATE_NO_SHOW])
    attended_count = cites.filter(state_cite=Cite.STATE_ATTENDED).count()
    no_show_count = cites.filter(state_cite=Cite.STATE_NO_SHOW).count()
    total = attended_count + no_show_count
    attendance_percentage = round((attended_count / total) * 100, 1) if total else 0.0
    no_show_percentage = round((no_show_count / total) * 100, 1) if total else 0.0
    return {
        'attended_count': attended_count,
        'no_show_count': no_show_count,
        'total': total,
        'attendance_percentage': attendance_percentage,
        'no_show_percentage': no_show_percentage,
    }


def _format_percentage(value):
    return f'{value:.1f}'.replace('.', ',')


@given('existen citas registradas en el sistema')
def step_given_existing_attendance_cites(context):
    _ensure_attendance_cites()
    context.expected_metrics = _compute_expected_metrics()
    assert context.expected_metrics['total'] > 0, (
        'La base de datos no tiene citas de asistencia para validar HU-38.'
    )


@given('el administrador inicia sesion en el sistema')
def step_given_admin_logs_in(context):
    context.credentials = _get_credentials()
    _ensure_admin_user(
        context.credentials['user'],
        context.credentials['password'],
    )
    context.login_page = LoginPage(context.driver)
    context.login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )
    WebDriverWait(context.driver, 10).until(
        lambda driver: '/login/' not in driver.current_url
    )


@given('el administrador accede al módulo de métricas')
def step_given_admin_opens_metrics_module(context):
    context.metrics_page = HU38AttendanceMetricsPage(context.driver)
    context.metrics_page.go_to_report(context.credentials['base_url'])
    context.metrics_page.wait_for_report()


@when('solicita el reporte de asistencia')
def step_when_request_attendance_report(context):
    context.metrics_page.go_to_report(context.credentials['base_url'])
    context.metrics_page.wait_for_report()


@when('el administrador revisa el reporte')
def step_when_admin_reviews_report(context):
    context.metrics_page.go_to_report(context.credentials['base_url'])
    context.metrics_page.wait_for_report()


@then('el sistema calcula las estadísticas correspondientes')
def step_then_system_calculates_stats(context):
    expected = context.expected_metrics
    assert context.metrics_page.total_text() == f"Total registros: {expected['total']}", (
        'El total de registros de asistencia no coincide con la base de datos.'
    )
    assert context.metrics_page.report_rows_count() == 2, (
        'El reporte debe mostrar dos filas: asistio y no asistio.'
    )


@then('el sistema muestra el porcentaje de asistencia de los usuarios')
def step_then_system_shows_percentage(context):
    expected = context.expected_metrics
    assert context.metrics_page.row_percentage_text('Asistió') == (
        f"{_format_percentage(expected['attendance_percentage'])}%"
    ), 'El porcentaje de asistencia no coincide con el calculado por el sistema.'
    assert context.metrics_page.row_percentage_text('No asistió') == (
        f"{_format_percentage(expected['no_show_percentage'])}%"
    ), 'El porcentaje de no asistencia no coincide con el calculado por el sistema.'
