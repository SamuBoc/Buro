from behave import given, when, then
from pages.reschedule_cite_page import RescheduleCite
from pages.do_login_page import LoginPage

@given('There is a cite assigned')
def step_given_cite_assigned(context):
    context.do_login_page = LoginPage(context.driver)
    context.reschedule_cite_page = RescheduleCite(context.driver)
    context.do_login_page.go_to_homepage()
    context.do_login_page.make_log_in()
    context.reschedule_cite_page.go_to_homepage()
    context.reschedule_cite_page.go_to_beneficiary_module()
    context.reschedule_cite_page.go_to_actions_user()
    context.reschedule_cite_page.go_to_cite_module()

@when('user changes date or hour')
def step_when_reschedule_cite(context):
    context.reschedule_cite_page.reschedule_cite()
    context.reschedule_cite_page.new_date()

@then('System updates cite information')
def step_then_check_reschedule(context):
    date = context.reschedule_cite_page.get_actual_date()

    assert date is not None and date == "1 de Enero de 2050 a las 01:00"