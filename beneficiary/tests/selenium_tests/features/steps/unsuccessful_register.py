from behave import given, when, then
from pages.register_beneficiary_pages import RegisterBeneficiarySelenium
from pages.do_login_page import LoginPage

# HU-1: Selenium test
@given('Secretariat access to register form beneficiary')
def step_given_form_beneficiary(context):
    context.do_login_page = LoginPage(context.driver)
    context.register_beneficiary_pages = RegisterBeneficiarySelenium(context.driver)
    context.do_login_page.go_to_homepage()
    context.do_login_page.make_log_in()
    context.register_beneficiary_pages.go_to_homepage()
    context.register_beneficiary_pages.go_to_beneficiary_module()
    context.register_beneficiary_pages.go_to_register()

@when('try registering a beneficiary without all the fields completed')
def step_when_complete_fields_form(context):
    context.register_beneficiary_pages.incomplete_fields()

@when('click in "Register" with empty fields')
def step_and_do_register(context):
    context.register_beneficiary_pages.make_register()

@then('System shows a message explaining that all the fields are necessary')
def step_then_check_empty_field(context):
    alert = context.register_beneficiary_pages.get_empty_alert()
    assert alert is not None and alert == "Este campo es obligatorio."