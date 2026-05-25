from datetime import timedelta

from behave import given, then, when
from django.contrib.auth.models import Group, User
from django.utils import timezone

from accounts.constants import ROLE_ESTUDIANTE, ROLE_PROFESOR
from beneficiary.models import Beneficiary
from cases.models import Case
from pages.academic_metrics_page import AcademicMetricsPage
from pages.login_page import LoginPage

PROF_USER = "profesor_selenium_hu27"
PROF_PASS = "selenium123"


def _ensure_professor():
    professor_group, _ = Group.objects.get_or_create(name=ROLE_PROFESOR)
    professor, created = User.objects.get_or_create(
        username=PROF_USER,
        defaults={
            "first_name": "Patricia",
            "last_name": "Selenium",
            "email": "patricia.selenium.hu27@test.com",
        },
    )
    if created:
        professor.set_password(PROF_PASS)
        professor.save()
    professor.groups.add(professor_group)
    return professor


def _ensure_student(username, first_name, student_code, preferred_room, supervising_professor):
    student_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)
    student, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": "HU27",
            "email": f"{username}@test.com",
        },
    )
    if created:
        student.set_password("selenium123")
        student.save()
    student.groups.add(student_group)
    profile = student.profile
    profile.student_code = student_code
    profile.max_cases = 5
    profile.availability = True
    profile.preferred_room = preferred_room
    profile.supervising_professor = supervising_professor
    profile.save()
    return student


def _make_beneficiary():
    beneficiary = Beneficiary.objects.filter(email="beneficiario.selenium.hu27@test.com").first()
    if beneficiary is None:
        beneficiary = Beneficiary.objects.create(
            name="Beneficiario Selenium HU27",
            email="beneficiario.selenium.hu27@test.com",
            phone="3031234567",
            colombian_identification="7788990011",
            location="Cali",
        )
    return beneficiary


def _ensure_case(description, student, beneficiary, sala, *, deadline_date, state):
    case = Case.objects.filter(description=description).order_by("-pk").first()
    if case is None:
        case = Case.objects.create(
            sala=sala,
            description=description,
            beneficiary=beneficiary,
            assigned_student=student,
            created_by=_ensure_professor(),
            state=state,
            status=Case.STATUS_COMPLETE,
            deadline_date=deadline_date,
        )
    else:
        case.sala = sala
        case.beneficiary = beneficiary
        case.assigned_student = student
        case.state = state
        case.status = Case.STATUS_COMPLETE
        case.deadline_date = deadline_date
        case.save()
    return case


@given("existen datos academicos registrados")
def step_academic_data_registered(context):
    professor = _ensure_professor()
    beneficiary = _make_beneficiary()
    today = timezone.localdate()

    student_one = _ensure_student(
        "hu27_estudiante_uno",
        "Laura",
        "HU27-001",
        Case.ROOM_CIVIL,
        professor,
    )
    student_two = _ensure_student(
        "hu27_estudiante_dos",
        "Miguel",
        "HU27-002",
        Case.ROOM_PENAL,
        professor,
    )

    case_one = _ensure_case(
        "Caso Selenium HU-27 civil.",
        student_one,
        beneficiary,
        Case.ROOM_CIVIL,
        deadline_date=today - timedelta(days=1),
        state=Case.STATE_ASSIGNED,
    )
    case_two = _ensure_case(
        "Caso Selenium HU-27 penal.",
        student_two,
        beneficiary,
        Case.ROOM_PENAL,
        deadline_date=None,
        state=Case.STATE_ASSIGNED,
    )

    context.hu27_professor = professor
    context.hu27_student_one = student_one
    context.hu27_student_two = student_two
    context.hu27_case_one = case_one
    context.hu27_case_two = case_two


@given("el profesor accede al modulo de metricas")
def step_professor_accesses_metrics(context):
    context.login_page = LoginPage(context.driver)
    context.metrics_page = AcademicMetricsPage(context.driver)
    context.login_page.login(PROF_USER, PROF_PASS)
    context.metrics_page.go_to_dashboard()


@when("aplica filtros por estudiante o tipo de caso")
def step_apply_student_case_type_filters(context):
    visible_text = context.hu27_student_two.get_full_name() or context.hu27_student_two.username
    context.metrics_page.filter_by_student_and_sala(
        student_visible_text=visible_text,
        sala_value=Case.ROOM_PENAL,
    )


@then("el sistema muestra las estadisticas correspondientes")
def step_dashboard_shows_filtered_stats(context):
    page_text = context.metrics_page.get_page_text()
    selected_student_name = context.hu27_student_two.get_full_name() or context.hu27_student_two.username
    other_student_name = context.hu27_student_one.get_full_name() or context.hu27_student_one.username
    table_text = "\n".join(context.metrics_page.get_table_rows_text())
    assert selected_student_name in table_text, "No se mostro el estudiante filtrado en la tabla del panel academico."
    assert other_student_name not in table_text, "La tabla del panel academico mostro estudiantes fuera del filtro aplicado."
    assert "Penal" in page_text, "No se reflejo la sala juridica filtrada en el dashboard."
    assert "Casos asignados" in page_text, "No se mostraron las metricas principales del dashboard."


@given("existen metricas registradas")
def step_existing_metrics_registered(context):
    step_academic_data_registered(context)
    context.login_page = LoginPage(context.driver)
    context.metrics_page = AcademicMetricsPage(context.driver)
    context.login_page.login(PROF_USER, PROF_PASS)


@when("el profesor revisa el desempeno del estudiante")
def step_professor_reviews_student_performance(context):
    context.metrics_page.go_to_student_detail(context.hu27_student_one.pk)


@then("el sistema muestra indicadores academicos asociados")
def step_student_performance_metrics_visible(context):
    page_text = context.metrics_page.get_page_text()
    assert "Desempeno del estudiante" in page_text, "No se abrio la vista de desempeno del estudiante."
    assert "Casos asignados" in page_text, "No se mostro el indicador de casos asignados."
    assert "Casos vencidos" in page_text, "No se mostro el indicador de casos vencidos."
    assert "Sin fecha limite" in page_text, "No se mostro el indicador de casos sin fecha limite."
    assert context.hu27_case_one.code in page_text, "No se mostro el caso esperado en el detalle de desempeno."
