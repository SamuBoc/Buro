from behave import given, when, then
from pages.register_beneficiary_pages import RegisterBeneficiarySelenium
from pages.do_login_page import LoginPage

# HU-3: Selenium test | Be sure you upload and avaible fiel to complete the selenium test

@given('register form beneficiary that have agreement policy')
def step_given_form_beneficiary(context):
    context.do_login_page = LoginPage(context.driver)
    context.register_beneficiary_pages = RegisterBeneficiarySelenium(context.driver)
    context.do_login_page.go_to_homepage()
    context.do_login_page.make_log_in()
    context.register_beneficiary_pages.go_to_homepage()
    context.register_beneficiary_pages.go_to_beneficiary_module()
    context.register_beneficiary_pages.go_to_register()

@when("registered all the info and don't mark Authorization option")
def step_when_complete_fields_form_without_mark_authorization(context):
    context.register_beneficiary_pages.dont_mark_authorization()

@when('click in "Register" to send form without Authorization')
def step_and_agree_register(context):
    context.register_beneficiary_pages.make_register()

@then('System shows a message that explain Authorization is necessary')
def step_then_check_empty_authorization(context):
    alert = context.register_beneficiary_pages.get_empty_alert()
    assert alert is not None and alert == "Este campo es obligatorio."