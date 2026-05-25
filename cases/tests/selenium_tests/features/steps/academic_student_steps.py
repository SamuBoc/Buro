from behave import given, then, when
from django.contrib.auth.models import Group, User

from accounts.constants import ROLE_ESTUDIANTE, ROLE_PROFESOR
from cases.models import Case
from pages.academic_student_page import AcademicStudentPage
from pages.login_page import LoginPage

ADMIN_USER = "admin_selenium"
ADMIN_PASS = "selenium123"


@given("el administrador accede al modulo academico")
def step_admin_accesses_academic_module(context):
    context.login_page = LoginPage(context.driver)
    context.academic_student_page = AcademicStudentPage(context.driver)
    context.login_page.login(ADMIN_USER, ADMIN_PASS)
    context.academic_student_page.go_to_register()


@given("el administrador ingresa los datos del estudiante")
def step_admin_enters_student_data(context):
    username = "selenium_hu25_student"
    student_code = "HU25-SEL-001"
    User.objects.filter(username=username).delete()

    context.hu25_student_payload = {
        "first_name": "Laura",
        "last_name": "Selenium",
        "email": "laura.selenium.hu25@test.com",
        "username": username,
        "student_code": student_code,
        "max_cases": 4,
        "preferred_room": "civil",
        "password": "selenium123",
        "availability": True,
    }
    context.academic_student_page.fill_registration_form(**context.hu25_student_payload)


@when("registra la carga academica correspondiente")
def step_register_student_load(context):
    context.academic_student_page.submit_registration()


@then("el sistema guarda la informacion del estudiante")
def step_student_information_saved(context):
    student = User.objects.filter(username=context.hu25_student_payload["username"]).first()
    assert student is not None, "No se encontro el estudiante registrado en la base de datos."
    assert student.groups.filter(name=ROLE_ESTUDIANTE).exists(), (
        "El estudiante registrado no quedo en el grupo estudiante."
    )
    assert student.profile.student_code == context.hu25_student_payload["student_code"], (
        "El codigo estudiantil guardado no coincide con el ingresado."
    )
    page_text = context.academic_student_page.get_page_text()
    assert "El estudiante fue registrado correctamente." in page_text, (
        "No se encontro el mensaje de exito del registro del estudiante."
    )
    assert context.hu25_student_payload["student_code"] in page_text, (
        "El listado no muestra el estudiante recien registrado."
    )


@given("existen estudiantes registrados")
def step_registered_students_exist(context):
    professor_group, _ = Group.objects.get_or_create(name=ROLE_PROFESOR)
    professor, _ = User.objects.get_or_create(username="profesor_selenium_hu25")
    if not professor.first_name:
        professor.first_name = "Paula"
        professor.last_name = "Supervisora"
        professor.email = "paula.supervisora.hu25@test.com"
        professor.set_password("selenium123")
        professor.save()
    professor.groups.add(professor_group)

    student_group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)
    student, created = User.objects.get_or_create(
        username="consulta_hu25_student",
        defaults={
            "first_name": "Carlos",
            "last_name": "Consulta",
            "email": "carlos.consulta.hu25@test.com",
        },
    )
    if created:
        student.set_password("selenium123")
        student.save()
    student.groups.add(student_group)
    student.profile.student_code = "HU25-SEL-002"
    student.profile.max_cases = 5
    student.profile.availability = True
    student.profile.preferred_room = "penal"
    student.profile.supervising_professor = professor
    student.profile.save()

    beneficiary = getattr(context, "selenium_beneficiary", None)
    assert beneficiary is not None, "No se preparo el beneficiario Selenium para HU-25."

    case, created_case = Case.objects.get_or_create(
        description="Caso Selenium HU-25 asignado para consulta academica.",
        defaults={
            "sala": Case.ROOM_PENAL,
            "beneficiary": beneficiary,
            "assigned_student": student,
            "created_by": User.objects.filter(username="secretaria_selenium").first(),
            "state": Case.STATE_ASSIGNED,
            "status": Case.STATUS_COMPLETE,
        },
    )
    if not created_case:
        case.sala = Case.ROOM_PENAL
        case.beneficiary = beneficiary
        case.assigned_student = student
        case.state = Case.STATE_ASSIGNED
        case.status = Case.STATUS_COMPLETE
        case.save()

    context.hu25_consult_student = student
    context.hu25_consult_case_code = case.code
    context.academic_student_page.go_to_list()


@when("el administrador consulta su informacion")
def step_admin_consults_student_info(context):
    context.academic_student_page.go_to_detail(context.hu25_consult_student.pk)


@then("el sistema muestra los casos asignados y su carga actual")
def step_system_shows_current_load(context):
    page_text = context.academic_student_page.get_page_text()
    assert "Casos activos" in page_text, "No se mostro la metrica de casos activos."
    assert "1" in page_text, "No se reflejo la carga actual esperada del estudiante."
    assert "Casos asignados" in page_text, "No se mostro la seccion de casos asignados."
    assert context.hu25_consult_case_code in page_text, (
        "No se mostro el caso asignado esperado en el detalle del estudiante."
    )
    assert "Asignado a estudiante" in page_text, "No se mostro el estado del caso asignado."
