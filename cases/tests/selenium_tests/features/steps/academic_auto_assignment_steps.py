import os
import tempfile

from behave import given, then, when
from django.contrib.auth.models import Group, User

from accounts.constants import ROLE_ESTUDIANTE
from beneficiary.models import Beneficiary
from cases.models import Case
from pages.case_access_page import CaseAccessPage
from pages.case_registration_page import CaseRegistrationPage
from pages.login_page import LoginPage

SEC_USER = "secretaria_selenium"
SEC_PASS = "selenium123"


def _build_test_document():
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "hu26_documento_soporte.pdf")
    if not os.path.exists(file_path):
        with open(file_path, "wb") as file_handle:
            file_handle.write(
                b"%PDF-1.4\n"
                b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
                b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]>>endobj\n"
                b"trailer<</Root 1 0 R>>\n%%EOF"
            )
    return file_path


def _create_academic_student(
    username,
    student_code,
    *,
    preferred_room,
    max_cases=5,
    availability=True,
):
    User.objects.filter(username=username).delete()
    user = User.objects.create_user(
        username=username,
        password="selenium123",
        email=f"{username}@test.com",
        first_name=username.replace("_", " ").title(),
    )
    group, _ = Group.objects.get_or_create(name=ROLE_ESTUDIANTE)
    user.groups.add(group)
    profile = user.profile
    profile.student_code = student_code
    profile.max_cases = max_cases
    profile.availability = availability
    profile.preferred_room = preferred_room
    profile.save()
    return user


def _disable_other_academic_students():
    student_group = Group.objects.filter(name=ROLE_ESTUDIANTE).first()
    if student_group is None:
        return

    students = (
        User.objects
        .filter(groups=student_group, profile__student_code__isnull=False)
        .exclude(profile__student_code="")
        .select_related("profile")
        .distinct()
    )
    for student in students:
        student.profile.availability = False
        student.profile.save(update_fields=["availability"])


def _create_support_case_for_student(student, beneficiary, description, *, sala):
    return Case.objects.create(
        sala=sala,
        description=description,
        beneficiary=beneficiary,
        assigned_student=student,
        created_by=User.objects.filter(username=SEC_USER).first(),
        state=Case.STATE_ASSIGNED,
        status=Case.STATUS_COMPLETE,
    )


@given("existen estudiantes registrados en el sistema")
def step_students_registered(context):
    context.login_page = LoginPage(context.driver)
    context.case_registration_page = CaseRegistrationPage(context.driver)
    context.case_access_page = CaseAccessPage(context.driver)

    context.login_page.login(SEC_USER, SEC_PASS)

    beneficiary = getattr(context, "selenium_beneficiary", None)
    assert beneficiary is not None, "No se preparo el beneficiario base Selenium para HU-26."
    context.hu26_beneficiary = beneficiary

    overload_beneficiary = Beneficiary.objects.filter(
        email="beneficiario.selenium.hu26@test.com"
    ).first()
    if overload_beneficiary is None:
        overload_beneficiary = Beneficiary.objects.create(
            name="Beneficiario Selenium HU26",
            email="beneficiario.selenium.hu26@test.com",
            phone="3021234567",
            colombian_identification="555667788",
            location="Cali",
        )
    context.hu26_load_beneficiary = overload_beneficiary


@given("se registra un nuevo caso")
def step_new_case_is_registered(context):
    Case.objects.filter(description__icontains="Selenium HU-26").delete()
    _disable_other_academic_students()

    context.hu26_best_student = _create_academic_student(
        "hu26_estudiante_ideal",
        "HU26-001",
        preferred_room=Case.ROOM_CIVIL,
        max_cases=5,
        availability=True,
    )
    _create_academic_student(
        "hu26_estudiante_otro",
        "HU26-002",
        preferred_room=Case.ROOM_PENAL,
        max_cases=5,
        availability=True,
    )

    context.hu26_case_description = "Caso Selenium HU-26 con afinidad civil."
    context.case_registration_page.go_to_case_create()
    context.case_registration_page.select_sala(Case.ROOM_CIVIL)
    context.case_registration_page.select_beneficiary_by_text(context.hu26_beneficiary.name)
    context.case_registration_page.fill_description(context.hu26_case_description)
    context.case_registration_page.upload_document(_build_test_document())
    context.case_registration_page.submit_complete()


@when("el sistema evalua los criterios de asignacion")
def step_system_evaluates_assignment(context):
    case_description = getattr(
        context,
        "hu26_case_description",
        getattr(context, "hu26_capacity_case_description", None),
    )
    assert case_description is not None, "No se definio la descripcion del caso Selenium HU-26."
    created_case = (
        Case.objects
        .filter(description=case_description)
        .order_by("-created_at", "-pk")
        .first()
    )
    assert created_case is not None, "No se encontro el caso Selenium HU-26 recien registrado."
    context.hu26_created_case = created_case


@then("asigna el caso al estudiante mas adecuado")
def step_case_assigned_to_best_student(context):
    context.hu26_created_case.refresh_from_db()
    assert context.hu26_created_case.assigned_student_id == context.hu26_best_student.id, (
        "El caso no fue asignado al estudiante con mejor afinidad academica."
    )
    page_text = context.case_access_page.get_page_text()
    expected_name = (
        context.hu26_best_student.get_full_name() or context.hu26_best_student.username
    )
    assert expected_name in page_text, (
        "El detalle del caso no muestra al estudiante seleccionado automaticamente."
    )


@given("un estudiante tiene su carga completa")
def step_student_at_full_load(context):
    Case.objects.filter(description__icontains="Selenium HU-26").delete()
    _disable_other_academic_students()

    context.hu26_full_student = _create_academic_student(
        "hu26_estudiante_lleno",
        "HU26-003",
        preferred_room=Case.ROOM_CIVIL,
        max_cases=1,
        availability=True,
    )
    context.hu26_available_student = _create_academic_student(
        "hu26_estudiante_disponible",
        "HU26-004",
        preferred_room=Case.ROOM_CIVIL,
        max_cases=5,
        availability=True,
    )
    _create_support_case_for_student(
        context.hu26_full_student,
        context.hu26_load_beneficiary,
        "Caso Selenium HU-26 que llena la carga.",
        sala=Case.ROOM_CIVIL,
    )

    context.hu26_capacity_case_description = "Caso Selenium HU-26 con estudiante lleno."
    context.case_registration_page.go_to_case_create()
    context.case_registration_page.select_sala(Case.ROOM_CIVIL)
    context.case_registration_page.select_beneficiary_by_text(context.hu26_beneficiary.name)
    context.case_registration_page.fill_description(context.hu26_capacity_case_description)
    context.case_registration_page.upload_document(_build_test_document())
    context.case_registration_page.submit_complete()


@then("el sistema selecciona otro estudiante disponible")
def step_selects_other_available_student(context):
    created_case = (
        Case.objects
        .filter(description=context.hu26_capacity_case_description)
        .order_by("-created_at", "-pk")
        .first()
    )
    assert created_case is not None, "No se encontro el caso creado para validar la carga completa."
    created_case.refresh_from_db()
    assert created_case.assigned_student_id == context.hu26_available_student.id, (
        "El sistema no selecciono al estudiante disponible cuando otro ya tenia la carga completa."
    )
    assert created_case.assigned_student_id != context.hu26_full_student.id, (
        "El sistema asigno el caso al estudiante que ya tenia la carga completa."
    )


@when("el sistema evalua la asignacion")
def step_system_evaluates_assignment_short(context):
    step_system_evaluates_assignment(context)
