from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base_page import BasePage


class CaseReassignmentPage(BasePage):
    CASE_LIST_TABLE = (By.ID, 'case-list-table')
    CASE_LIST_EMPTY = (By.ID, 'case-list-empty')
    CASE_DETAIL_LINKS = (By.CSS_SELECTOR, '.case-detail-link')
    CASE_DETAIL_CONTAINER = (By.ID, 'case-detail')
    ASSIGNED_STUDENT_TEXT = (By.ID, 'case-assigned-student')
    REASSIGN_FORM = (By.ID, 'case-reassign-form')
    REASSIGN_SELECT = (By.ID, 'id_assigned_student')
    REASSIGN_SUBMIT = (By.ID, 'case-reassign-submit')
    REASSIGN_LOG = (By.ID, 'case-reassign-log')
    NO_PERMISSION_TITLE = (By.XPATH, "//h3[contains(., 'Acceso restringido')]")
    NO_PERMISSION_MESSAGE = (By.XPATH, "//p[contains(., 'No cuentas con los permisos')]")

    def go_to_case_list(self, base_url):
        self.driver.get(f"{base_url}/casos/")

    def wait_for_case_list(self):
        def _ready(driver):
            return (
                driver.find_elements(*self.CASE_LIST_TABLE)
                or driver.find_elements(*self.CASE_LIST_EMPTY)
            )

        WebDriverWait(self.driver, self.timeout).until(_ready)
        tables = self.driver.find_elements(*self.CASE_LIST_TABLE)
        return tables[0] if tables else None

    def open_first_case_detail(self):
        self.wait_for_case_list()
        links = self.driver.find_elements(*self.CASE_DETAIL_LINKS)
        if not links:
            return False
        links[0].click()
        return True

    def get_first_case_detail_url(self):
        self.wait_for_case_list()
        links = self.driver.find_elements(*self.CASE_DETAIL_LINKS)
        if not links:
            return None
        return links[0].get_attribute('href')

    def wait_for_detail(self):
        return self.find_element(self.CASE_DETAIL_CONTAINER)

    def get_case_id_from_url(self):
        current_url = self.driver.current_url.rstrip('/')
        return current_url.split('/')[-1]

    def go_to_case_detail(self, base_url, case_id):
        self.driver.get(f"{base_url}/casos/{case_id}/")

    def go_to_reassign(self, base_url, case_id):
        self.driver.get(f"{base_url}/casos/{case_id}/reasignar/")

    def select_different_student(self):
        select = Select(self.find_element(self.REASSIGN_SELECT))
        current_value = select.first_selected_option.get_attribute('value')
        for option in select.options:
            option_value = option.get_attribute('value')
            if option_value and option_value != current_value:
                select.select_by_value(option_value)
                return option.text.strip()
        return None

    def submit_reassign(self):
        self.click_js(self.REASSIGN_SUBMIT)

    def assigned_student_text(self):
        return self.find_element(self.ASSIGNED_STUDENT_TEXT).text.strip()

    def log_has_entries(self):
        container = self.find_element(self.REASSIGN_LOG)
        items = container.find_elements(By.CSS_SELECTOR, '.list-group-item')
        return len(items) > 0

    def log_contains_text(self, text):
        container = self.find_element(self.REASSIGN_LOG)
        items = container.find_elements(By.CSS_SELECTOR, '.list-group-item')
        return any(text in item.text for item in items)

    def no_permission_visible(self):
        self.find_element(self.NO_PERMISSION_TITLE)

    def no_permission_message_visible(self):
        self.find_element(self.NO_PERMISSION_MESSAGE)
