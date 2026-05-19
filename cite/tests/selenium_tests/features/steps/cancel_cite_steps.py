from behave import given, when, then
from pages.cancel_cite_page import CancelCite
from pages.do_login_page import LoginPage

@given('There is a cite assigned previously')
def step_given_cite_assigned(context):
    context.do_login_page = LoginPage(context.driver)
    context.cancel_cite_page = CancelCite(context.driver)
    context.do_login_page.go_to_homepage()
    context.do_login_page.make_log_in("stevan", "useruser")
    context.cancel_cite_page.go_to_homepage()
    context.cancel_cite_page.go_to_beneficiary_module()
    context.cancel_cite_page.go_to_actions_user()
    context.cancel_cite_page.go_to_cite_module()

@when('user selects cancel cite')
def step_when_cancel_cite(context):
    context.cancel_cite_page.cancel_cite()

@then('System update cite state to "Cancelada"')
def step_then_check_reschedule(context, state = "Cancelada"):
    actual_state = context.cancel_cite_page.get_state_cite()

    assert actual_state is not None and actual_state == state