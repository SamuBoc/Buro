import os
import tempfile

from behave import given, then, when

from beneficiary.models import Beneficiary
from cases.models import Case
from pages.case_registration_page import CaseRegistrationPage
from pages.login_page import LoginPage
from django.contrib.auth.models import User

SEC_USER = "secretaria_selenium"
SEC_PASS = "selenium123"


def _build_test_document():
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "hu6_documento_soporte.pdf")
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


@given("la secretaria ha iniciado sesion en el sistema")
def step_secretaria_logged_in(context):
    context.login_page = LoginPage(context.driver)
    context.case_registration_page = CaseRegistrationPage(context.driver)
    context.login_page.login(SEC_USER, SEC_PASS)


@given("existe un beneficiario previamente registrado")
def step_existing_beneficiary(context):
    beneficiary = getattr(context, "selenium_beneficiary", None)
    assert beneficiary is not None, "No se preparo el beneficiario Selenium para HU-6."
    context.beneficiary = beneficiary


@given("la secretaria accede al formulario de registro de caso")
def step_open_case_registration_form(context):
    selenium_secretary = User.objects.get(username=SEC_USER)
    Case.objects.filter(
        created_by=selenium_secretary,
        status=Case.STATUS_DRAFT,
    ).delete()
    context.case_registration_page.go_to_case_create()
    context.initial_case_count = Case.objects.count()


@given("la secretaria intenta registrar un caso")
def step_prepare_invalid_case_submission(context):
    context.case_registration_page.select_beneficiary_by_text(context.beneficiary.name)
    context.case_registration_page.upload_document(_build_test_document())


@when("selecciona la sala juridica")
def step_select_room(context):
    context.case_registration_page.select_sala("civil")


@when("ingresa la descripcion del problema")
def step_fill_description(context):
    context.case_description = "Caso Selenium HU-6 sobre conflicto contractual civil."
    context.case_registration_page.select_beneficiary_by_text(context.beneficiary.name)
    context.case_registration_page.fill_description(context.case_description)


@when("carga los documentos soporte")
def step_upload_support_documents(context):
    context.case_registration_page.upload_document(_build_test_document())


@when('hace clic en "Registrar caso"')
def step_submit_case(context):
    context.case_registration_page.submit_complete()


@then("el sistema guarda la informacion del caso")
def step_case_is_saved(context):
    assert context.case_registration_page.current_url_is_case_detail(), (
        f"Se esperaba redireccion al detalle del caso, URL actual: "
        f"{context.driver.current_url}"
    )
    context.created_case = Case.objects.order_by("-created_at").first()
    assert context.created_case is not None, "No se encontro ningun caso creado."
    assert Case.objects.count() == context.initial_case_count + 1, (
        "La cantidad de casos no aumento tras registrar el caso."
    )
    assert context.created_case.description == context.case_description, (
        "La descripcion del caso no coincide con la ingresada en el formulario."
    )


@then("asocia el caso al beneficiario correspondiente")
def step_case_is_linked_to_beneficiary(context):
    assert context.created_case.beneficiary_id == context.beneficiary.pk, (
        "El caso no quedo asociado al beneficiario esperado."
    )


@when("no selecciona la sala juridica o no ingresa la descripcion")
def step_submit_missing_required_fields(context):
    context.case_registration_page.submit_complete_with_native_click()


@then(
    "el sistema muestra un mensaje indicando que los campos obligatorios deben completarse"
)
def step_validation_message_is_shown(context):
    page_text = context.case_registration_page.get_page_text().lower()
    active_validation_message = (
        context.case_registration_page.get_active_validation_message() or ""
    ).strip()
    active_element_id = context.case_registration_page.get_active_element_id() or ""
    form_is_valid = context.case_registration_page.form_is_valid()
    current_url = context.driver.current_url
    assert (
        "por favor corrija los errores del formulario" in page_text
        or "este campo es obligatorio" in page_text
        or active_validation_message
        or (not form_is_valid and active_element_id in {"id_sala", "id_description"})
        or "/casos/registrar/" in current_url
    ), (
        "No se encontro el mensaje esperado de validacion de campos obligatorios. "
        f"URL={current_url} active_id={active_element_id} "
        f"active_validation={active_validation_message!r} form_is_valid={form_is_valid} "
        f"body={page_text[:300]!r}"
    )


@then("no permite registrar el caso")
def step_case_is_not_saved(context):
    assert not context.case_registration_page.current_url_is_case_detail(), (
        "No deberia haberse redirigido al detalle de un caso cuando faltan obligatorios."
    )
    assert Case.objects.count() == context.initial_case_count, (
        "Se creo un caso aun cuando faltaban campos obligatorios."
    )
