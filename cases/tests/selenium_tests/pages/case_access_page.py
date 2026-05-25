from selenium.webdriver.common.by import By
import re

from .base_page import BasePage, BASE_URL


class CaseAccessPage(BasePage):
    DETAIL_HEADER = (By.TAG_NAME, "h4")
    ALERTS = (By.CSS_SELECTOR, ".alert")

    def go_to_case_detail(self, case_id):
        self.driver.get(f"{BASE_URL}/casos/{case_id}/")

    def get_page_text(self):
        return self.driver.find_element(By.TAG_NAME, "body").text

    def current_url_is_case_detail(self, case_id):
        expected_url = f"{BASE_URL}/casos/{case_id}/"
        normalized_current = self.driver.current_url.rstrip("/")
        normalized_expected = expected_url.rstrip("/")
        return normalized_current == normalized_expected

    def is_in_case_list(self):
        return bool(re.search(r"/casos/?$", self.driver.current_url))

    def has_permission_alert(self):
        body_text = self.get_page_text().lower()
        return "no tienes permisos para acceder a este caso" in body_text
