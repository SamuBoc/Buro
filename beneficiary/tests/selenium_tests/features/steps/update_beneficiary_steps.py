from behave import given, when, then
from pages.update_beneficiary_pages import UpdateBeneficiarySelenium
from pages.do_login_page import LoginPage

# HU-5: Selenium test
# Be sure you register a beneficiary before

@given('Secretariat access to beneficiary profile')
def step_given_form_update_beneficiary(context):
    context.do_login_page = LoginPage(context.driver)
    context.update_beneficiary_pages = UpdateBeneficiarySelenium(context.driver)
    context.do_login_page.go_to_homepage()
    context.do_login_page.make_log_in()
    context.update_beneficiary_pages.go_to_homepage()
    context.update_beneficiary_pages.go_to_beneficiary_module()
    context.update_beneficiary_pages.beneficiary_details()
    context.update_beneficiary_pages.go_to_update()

@when('makes one or more personal data modifications')
def step_when_complete_some_fields(context):
    context.update_beneficiary_pages.modify_some_fields()

@when('click in "Save Changes"')
def step_and_agree_register(context):
    context.update_beneficiary_pages.make_update()

@then('System Update beneficiary information')
def step_then_check_info(context):
    context.update_beneficiary_pages.beneficiary_details()
    location = context.update_beneficiary_pages.get_location_modified()
    phone = context.update_beneficiary_pages.get_phone_modified()
    assert location is not None and location == "Ciudad Pesadilla, ICESI"
    assert phone is not None and phone == "911"

@then('is recording in binnacle')
def step_then_check_binnacle(context):

    # Binnacle
    context.update_beneficiary_pages.go_to_binnacle()
    action_done = context.update_beneficiary_pages.get_action_done()
    assert action_done is not None and action_done == "Datos actualizados"