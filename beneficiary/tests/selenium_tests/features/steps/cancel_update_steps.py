from behave import given, when, then
from pages.update_beneficiary_pages import UpdateBeneficiarySelenium
from pages.do_login_page import LoginPage

# HU-5: Selenium test
# Be sure you register a beneficiary before

@given("Secretariat it's making changes to beneficiary")
def step_given_form_update_beneficiary(context):
    context.do_login_page = LoginPage(context.driver)
    context.update_beneficiary_pages = UpdateBeneficiarySelenium(context.driver)
    context.do_login_page.go_to_homepage()
    context.do_login_page.make_log_in()
    context.update_beneficiary_pages.go_to_homepage()
    context.update_beneficiary_pages.go_to_beneficiary_module()
    context.update_beneficiary_pages.beneficiary_details()
    context.update_beneficiary_pages.go_to_update()
    context.update_beneficiary_pages.modify_some_fields_to_cancel()

@when('click in "Cancel"')
def step_when_cancel_modifications(context):
    context.update_beneficiary_pages.cancel_update()

@then("System don't make modifications to beneficiary")
def step_then_check_info(context):
    context.update_beneficiary_pages.beneficiary_details()
    name = context.update_beneficiary_pages.get_name()
    assert name is not None