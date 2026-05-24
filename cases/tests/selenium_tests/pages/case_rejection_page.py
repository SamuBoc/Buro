from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class CaseRejectionPage(BasePage):
    CASE_LIST_TABLE = (By.ID, 'case-list-table')
    CASE_LIST_EMPTY = (By.ID, 'case-list-empty')
    CASE_DETAIL_LINKS = (By.CSS_SELECTOR, '.case-detail-link')
    CASE_DETAIL_CONTAINER = (By.ID, 'case-detail')
    CASE_STATE = (By.ID, 'case-state')
    CASE_REJECTION_REASON = (By.ID, 'case-rejection-reason')
    REJECT_FORM = (By.ID, 'case-reject-form')
    REJECT_REASON_INPUT = (By.ID, 'id_rejection_reason')
    REJECT_SUBMIT = (By.ID, 'case-reject-submit')
    REJECT_ERROR = (By.ID, 'case-reject-error')

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

    def open_case_with_reject_form(self, base_url, case_id=None):
        if case_id:
            self.go_to_case_detail(base_url, case_id)
            self.wait_for_detail()
            return self.has_reject_form()

        self.go_to_case_list(base_url)
        try:
            self.wait_for_case_list()
        except TimeoutException:
            return False

        links = self.driver.find_elements(*self.CASE_DETAIL_LINKS)
        hrefs = [link.get_attribute('href') for link in links if link.get_attribute('href')]
        for href in hrefs:
            self.driver.get(href)
            self.wait_for_detail()
            if self.has_reject_form():
                return True
        return False

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

    def wait_for_reject_form(self):
        return self.find_element(self.REJECT_FORM)

    def has_reject_form(self):
        return bool(self.driver.find_elements(*self.REJECT_FORM))

    def enter_rejection_reason(self, text):
        element = self.find_element(self.REJECT_REASON_INPUT)
        element.clear()
        element.send_keys(text)

    def submit_reject(self):
        self.click_js(self.REJECT_SUBMIT)

    def state_text(self):
        return self.find_element(self.CASE_STATE).text.strip()

    def rejection_reason_text(self):
        return self.find_element(self.CASE_REJECTION_REASON).text.strip()

    def rejection_error_visible(self):
        self.find_element(self.REJECT_ERROR)
