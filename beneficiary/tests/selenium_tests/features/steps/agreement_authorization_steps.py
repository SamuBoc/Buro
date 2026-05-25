from behave import given, when, then
from pages.register_beneficiary_pages import RegisterBeneficiarySelenium
from pages.do_login_page import LoginPage

# HU-3: Selenium test | Be sure you upload and avaible fiel to complete the selenium test

@given('Secretariat access to register form beneficiary that have agreement policy')
def step_given_form_beneficiary(context):
    context.do_login_page = LoginPage(context.driver)
    context.register_beneficiary_pages = RegisterBeneficiarySelenium(context.driver)
    context.do_login_page.go_to_homepage()
    context.do_login_page.make_log_in()
    context.register_beneficiary_pages.go_to_homepage()
    context.register_beneficiary_pages.go_to_beneficiary_module()
    context.register_beneficiary_pages.go_to_register()

@when('registered all the info and mark Authorization option')
def step_when_complete_fields_form(context):
    context.register_beneficiary_pages.complete_fields()

@when('click in "Register" to send form')
def step_and_agree_register(context):
    context.register_beneficiary_pages.make_register()

@then('System allows make the register')
def step_then_check_info(context):
    data = context.register_beneficiary_pages.get_data()
    assert data is not None