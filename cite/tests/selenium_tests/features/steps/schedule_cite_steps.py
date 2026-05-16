from behave import given, when, then
from pages.schedule_cite_page import ScheduleCite
from pages.do_login_page import LogIn

@given('Secretariat goes to cite module')
def step_given_module_cite(context):
    context.schedule_cite_page = ScheduleCite(context.driver)
    context.do_login_page = LogIn(context.driver)
    context.do_login_page.go_to_homepage()
    context.do_login_page.make_log_in()
    context.schedule_cite_page.go_to_homepage()
    context.schedule_cite_page.go_to_beneficiary_module()
    context.schedule_cite_page.go_to_actions_user()
    context.schedule_cite_page.go_to_cite_form()

@when('Select an avaible date and hour')
def step_when_select_date(context):
    context.schedule_cite_page.define_date_cite()

@when('And Confirm schedule')
def step_and_confirm_schedule(context):
    context.schedule_cite_page.send_form()

@then('Then System register a new cite')
def step_then_check_date_assigment(context):
    context.schedule_cite_page.go_to_cite_module()
    date = context.schedule_cite_page.get_date_assigment()

    assert date is not None and date == "31/05/2026"