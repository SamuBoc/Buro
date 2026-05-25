from behave import given, when, then
from pages.register_beneficiary_pages import RegisterBeneficiarySelenium
from pages.do_login_page import LoginPage

# HU-1: Selenium test

@given('Secretariat access to register form')
def step_given_form_beneficiary(context):
    context.do_login_page = LoginPage(context.driver)
    context.register_beneficiary_pages = RegisterBeneficiarySelenium(context.driver)
    context.do_login_page.go_to_homepage()
    context.do_login_page.make_log_in()
    context.register_beneficiary_pages.go_to_homepage()
    context.register_beneficiary_pages.go_to_beneficiary_module()
    context.register_beneficiary_pages.go_to_register()

@when('enters name, document, direction, phone, mail, agreement with private policts and document file')
def step_when_complete_fields_form(context):
    context.register_beneficiary_pages.complete_fields()

@when('click in "Register"')
def step_and_agree_register(context):
    context.register_beneficiary_pages.make_register()

@then('System save Beneficiary record')
def step_then_check_info(context):
    data = context.register_beneficiary_pages.get_data()
    assert data is not None