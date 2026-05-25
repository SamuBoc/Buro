from behave import given, then, when
from django.contrib.auth.models import User

from beneficiary.models import DataDeletionRequest
from pages.data_deletion_page import DataDeletionPage
from pages.login_page import LoginPage

SEC_USER = "secretaria_selenium"
SEC_PASS = "selenium123"
ADMIN_USER = "admin_selenium"
ADMIN_PASS = "selenium123"


@given("el beneficiario tiene datos registrados en el sistema")
def step_beneficiary_registered(context):
    beneficiary = getattr(context, "selenium_hu34_beneficiary", None)
    assert beneficiary is not None, "No se preparo el beneficiario Selenium para HU-34."
    context.hu34_beneficiary = beneficiary
    DataDeletionRequest.objects.filter(beneficiary=beneficiary).delete()


@given("el usuario accede a su perfil")
def step_user_accesses_profile(context):
    context.login_page = LoginPage(context.driver)
    context.data_deletion_page = DataDeletionPage(context.driver)
    context.login_page.login(SEC_USER, SEC_PASS)
    context.data_deletion_page.go_to_beneficiary_detail(context.hu34_beneficiary.pk)


@when("solicita la eliminacion de sus datos")
def step_request_data_deletion(context):
    context.deletion_reason = "Solicitud Selenium HU-34 para eliminar datos personales."
    context.data_deletion_page.click_request_deletion()
    context.data_deletion_page.fill_reason(context.deletion_reason)
    context.data_deletion_page.confirm_request()
    context.data_deletion_page.submit_request()


@then("el sistema registra la solicitud")
def step_request_registered(context):
    request_obj = DataDeletionRequest.objects.filter(
        beneficiary=context.hu34_beneficiary
    ).order_by("-request_date", "-pk").first()
    assert request_obj is not None, "No se encontro la solicitud de eliminacion registrada."
    assert request_obj.reason == context.deletion_reason, (
        "El motivo registrado no coincide con el ingresado en el formulario."
    )
    page_text = context.data_deletion_page.get_page_text().lower()
    assert "la solicitud de eliminacion de datos fue registrada correctamente" in page_text, (
        "No se encontro el mensaje de confirmacion esperado en la interfaz."
    )


@given("se ha realizado una solicitud de eliminacion")
def step_existing_deletion_request(context):
    beneficiary = context.hu34_beneficiary
    request_obj, _ = DataDeletionRequest.objects.get_or_create(
        beneficiary=beneficiary,
        defaults={
            "reason": "Solicitud Selenium HU-34 ya registrada.",
            "status": DataDeletionRequest.STATUS_PENDING,
        },
    )
    if request_obj.reason != "Solicitud Selenium HU-34 ya registrada.":
        request_obj.reason = "Solicitud Selenium HU-34 ya registrada."
        request_obj.status = DataDeletionRequest.STATUS_PENDING
        request_obj.save(update_fields=["reason", "status"])
    context.hu34_request = request_obj


@when("el administrador revisa las solicitudes")
def step_admin_reviews_requests(context):
    context.login_page = LoginPage(context.driver)
    context.data_deletion_page = DataDeletionPage(context.driver)
    context.login_page.login(ADMIN_USER, ADMIN_PASS)
    context.data_deletion_page.go_to_request_list()


@then("el sistema muestra la solicitud registrada")
def step_request_visible_in_list(context):
    page_text = context.data_deletion_page.get_page_text()
    assert context.hu34_beneficiary.name in page_text, (
        "La lista no muestra el beneficiario de la solicitud registrada."
    )
    assert context.hu34_request.reason in page_text, (
        "La lista no muestra el motivo de la solicitud registrada."
    )
