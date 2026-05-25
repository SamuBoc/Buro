from behave import given, then, when
from django.contrib.auth.models import User

from cases.models import Case
from pages.case_registration_page import CaseRegistrationPage
from pages.login_page import LoginPage

SEC_USER = "secretaria_selenium"
SEC_PASS = "selenium123"


@given("el usuario esta completando un formulario en el sistema")
def step_user_is_completing_form(context):
    context.login_page = LoginPage(context.driver)
    context.case_registration_page = CaseRegistrationPage(context.driver)
    context.login_page.login(SEC_USER, SEC_PASS)

    secretaria = User.objects.get(username=SEC_USER)
    Case.objects.filter(
        created_by=secretaria,
        status=Case.STATUS_DRAFT,
        description__icontains="selenium hu-32",
    ).delete()

    context.case_registration_page.go_to_case_create()


@given("el usuario ha ingresado datos parciales")
def step_user_entered_partial_data(context):
    context.partial_description = "Borrador Selenium HU-32 con datos parciales."
    context.case_registration_page.fill_description(context.partial_description)


@when("selecciona la opcion guardar borrador")
def step_save_draft(context):
    context.case_registration_page.submit_draft()


@then("el sistema almacena la informacion ingresada")
def step_draft_is_stored(context):
    secretaria = User.objects.get(username=SEC_USER)
    draft_qs = (
        Case.objects
        .filter(created_by=secretaria)
        .order_by("-created_at", "-pk")
    )
    draft_case = draft_qs.filter(status=Case.STATUS_DRAFT).first()
    assert draft_case is not None, "No se encontro un borrador guardado para la secretaria."
    assert draft_case.description == context.partial_description, (
        "La descripcion almacenada en el borrador no coincide con la ingresada."
    )
    page_text = context.case_registration_page.get_page_text().lower()
    assert "borrador" in page_text, "No se encontro retroalimentacion visual del borrador en la pagina."


@given("existe un borrador guardado")
def step_existing_saved_draft(context):
    secretaria = User.objects.get(username=SEC_USER)
    beneficiary = getattr(context, "selenium_beneficiary", None)
    assert beneficiary is not None, "No se preparo el beneficiario Selenium para HU-32."

    Case.objects.filter(
        created_by=secretaria,
        status=Case.STATUS_DRAFT,
        description__icontains="selenium hu-32",
    ).delete()

    context.saved_draft_description = "Texto recuperado Selenium HU-32."
    context.saved_draft = Case.objects.create(
        sala=Case.ROOM_CIVIL,
        description=context.saved_draft_description,
        beneficiary=beneficiary,
        created_by=secretaria,
        status=Case.STATUS_DRAFT,
    )


@when("el usuario vuelve a abrir el formulario")
def step_user_reopens_form(context):
    context.case_registration_page.go_to_case_create()


@then("el sistema muestra los datos previamente guardados")
def step_saved_data_is_shown(context):
    description_value = context.case_registration_page.get_description_value()
    assert description_value == context.saved_draft_description, (
        "El formulario no mostro la descripcion previamente guardada en el borrador."
    )
    page_text = context.case_registration_page.get_page_text().lower()
    assert "tienes un borrador pendiente" in page_text or "estas continuando el borrador" in page_text, (
        "No se encontro el mensaje de recuperacion del borrador en la interfaz."
    )
