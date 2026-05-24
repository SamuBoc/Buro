from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class CaseDeadlinePage(BasePage):
    CASE_LIST_TABLE = (By.ID, 'case-list-table')
    CASE_LIST_EMPTY = (By.ID, 'case-list-empty')
    CASE_DETAIL_LINKS = (By.CSS_SELECTOR, '.case-detail-link')
    CASE_DETAIL_CONTAINER = (By.ID, 'case-detail')

    DEADLINE_INPUT = (By.ID, 'id_deadline_date')
    DEADLINE_FORM = (By.ID, 'case-deadline-form')
    DEADLINE_SUBMIT = (By.ID, 'case-deadline-submit')
    DEADLINE_TEXT = (By.ID, 'case-deadline-date')

    NOTIF_TITLE = (By.CSS_SELECTOR, '.notif-page-card-title')

    CASE_CODE = (By.XPATH, "//small[contains(., 'Codigo:')]")

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

    def go_to_case_detail(self, base_url, case_id):
        self.driver.get(f"{base_url}/casos/{case_id}/")

    def wait_for_detail(self):
        return self.find_element(self.CASE_DETAIL_CONTAINER)

    def get_case_id_from_url(self):
        current_url = self.driver.current_url.rstrip('/')
        return current_url.split('/')[-1]

    def get_case_code(self):
        text = self.find_element(self.CASE_CODE).text.strip()
        return text.replace('Codigo:', '').strip()

    def set_deadline(self, date_value):
        element = self.find_element(self.DEADLINE_INPUT)
        self.driver.execute_script(
            """
            const input = arguments[0];
            const value = arguments[1];
            input.value = value;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            """,
            element,
            date_value,
        )

    def submit_deadline(self):
        self.click_js(self.DEADLINE_SUBMIT)

    def deadline_text(self):
        return self.find_element(self.DEADLINE_TEXT).text.strip()

    def go_to_notifications(self, base_url):
        self.driver.get(f"{base_url}/casos/notificaciones/")

    def has_notification_title(self, expected_text):
        titles = self.driver.find_elements(*self.NOTIF_TITLE)
        return any(expected_text in title.text for title in titles)
