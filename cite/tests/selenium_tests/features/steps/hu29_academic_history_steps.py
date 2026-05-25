import os
import sys

from behave import given, when, then
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django

django.setup()

from django.contrib.auth.models import Group, User

from accounts.constants import ROLE_ADMINISTRADOR, ROLE_ESTUDIANTE, ROLE_PROFESOR
from beneficiary.models import Beneficiary
from cases.models import Case, CaseEvaluation, CaseReassignmentLog

from pages.do_login_page import LoginPage
from pages.hu29_academic_history_page import HU29AcademicHistoryPage


def _get_credentials():
    return {
        'user': os.getenv('HU29_PROFESSOR_USER', 'profesor_hu29'),
        'password': os.getenv('HU29_PROFESSOR_PASSWORD', 'ClaveHu29!'),
        'base_url': os.getenv('SELENIUM_BASE_URL', 'http://127.0.0.1:8000'),
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


def _ensure_student(username, password, student_code):
    student = _ensure_user_with_role(username, password, ROLE_ESTUDIANTE)
    if not student.profile.student_code:
        student.profile.student_code = student_code
        student.profile.save()
    return student


def _ensure_case(beneficiary, description, assigned_student):
    case = Case.objects.filter(
        beneficiary=beneficiary,
        description=description,
    ).first()
    if case:
        case.assigned_student = assigned_student
        case.status = Case.STATUS_COMPLETE
        case.state = Case.STATE_ASSIGNED
        case.save(update_fields=['assigned_student', 'status', 'state'])
        return case

    return Case.objects.create(
        sala=Case.ROOM_CIVIL,
        description=description,
        beneficiary=beneficiary,
        assigned_student=assigned_student,
        status=Case.STATUS_COMPLETE,
        state=Case.STATE_ASSIGNED,
    )


def _ensure_history_data(context):
    professor = _ensure_user_with_role(
        context.credentials['user'],
        context.credentials['password'],
        ROLE_PROFESOR,
    )
    admin = _ensure_user_with_role('admin_hu29', 'ClaveAdminHu29!', ROLE_ADMINISTRADOR)
    student = _ensure_student('estudiante_hu29', 'ClaveEstudianteHu29!', '20262901')
    other_student = _ensure_student('estudiante_hu29_b', 'ClaveEstudianteHu29!', '20262902')

    beneficiary, _ = Beneficiary.objects.update_or_create(
        id='BEN-HU29-0001',
        defaults={
            'name': 'Beneficiario HU29',
            'location': 'Cali',
            'email': 'hu29_beneficiary@test.com',
            'colombian_identification': '1020304050',
            'phone': '3001122334',
        },
    )

    active_case = _ensure_case(beneficiary, 'Caso activo HU29', student)
    historic_case = _ensure_case(beneficiary, 'Caso historico HU29', student)

    if historic_case.assigned_student_id != other_student.id:
        old_student = historic_case.assigned_student
        historic_case.assigned_student = other_student
        historic_case.save(update_fields=['assigned_student'])
    else:
        old_student = student

    CaseReassignmentLog.objects.get_or_create(
        case=historic_case,
        old_student=old_student,
        new_student=other_student,
        changed_by=admin,
    )

    evaluation, _ = CaseEvaluation.objects.get_or_create(
        case=active_case,
        student=student,
        defaults={
            'professor': professor,
            'score': 4,
            'feedback': 'Buen manejo del caso y comunicacion con el beneficiario.',
        },
    )

    context.professor = professor
    context.student = student
    context.active_case = active_case
    context.historic_case = historic_case
    context.evaluation = evaluation


@given('existe un estudiante registrado')
def step_given_student_registered(context):
    context.credentials = _get_credentials()
    _ensure_history_data(context)


@given('el profesor accede al perfil del estudiante')
def step_given_professor_accesses_profile(context):
    context.login_page = LoginPage(context.driver)
    context.history_page = HU29AcademicHistoryPage(context.driver)

    context.login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
    context.login_page.make_log_in(
        context.credentials['user'],
        context.credentials['password'],
    )
    WebDriverWait(context.driver, 10).until(
        lambda driver: '/login/' not in driver.current_url
    )

    context.history_page.go_to_history(
        context.credentials['base_url'],
        context.student.pk,
    )
    context.history_page.wait_for_history()


@when('consulta su historial academico')
def step_when_review_history(context):
    context.history_page.wait_for_history()


@then('el sistema muestra los casos gestionados y evaluaciones')
def step_then_show_cases_and_evaluations(context):
    assert context.history_page.text_visible(
        context.active_case.code
    ), 'No se encontro el caso activo en el historial.'
    assert context.history_page.text_visible(
        context.historic_case.code
    ), 'No se encontro el caso historico en el historial.'
    assert context.history_page.text_visible(
        context.evaluation.feedback
    ), 'No se encontro la evaluacion registrada en el historial.'


@given('existen evaluaciones registradas')
def step_given_evaluations_exist(context):
    if not hasattr(context, 'student'):
        context.credentials = _get_credentials()
        _ensure_history_data(context)


@when('el profesor revisa el historial')
def step_when_professor_reviews_history(context):
    if not hasattr(context, 'history_page'):
        context.login_page = LoginPage(context.driver)
        context.history_page = HU29AcademicHistoryPage(context.driver)

        context.login_page.go_to_homepage(f"{context.credentials['base_url']}/login/")
        context.login_page.make_log_in(
            context.credentials['user'],
            context.credentials['password'],
        )
        WebDriverWait(context.driver, 10).until(
            lambda driver: '/login/' not in driver.current_url
        )

        context.history_page.go_to_history(
            context.credentials['base_url'],
            context.student.pk,
        )

    context.history_page.wait_for_history()


@then('el sistema muestra la retroalimentacion correspondiente')
def step_then_show_feedback(context):
    assert context.history_page.text_visible(
        context.evaluation.feedback
    ), 'No se encontro la retroalimentacion en el historial.'
