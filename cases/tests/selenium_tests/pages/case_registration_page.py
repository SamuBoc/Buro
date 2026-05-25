import os
import re

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base_page import BasePage, BASE_URL


class CaseRegistrationPage(BasePage):
    SALA_SELECT = (By.ID, "id_sala")
    BENEFICIARY_SELECT = (By.ID, "id_beneficiary")
    DESCRIPTION_TEXTAREA = (By.ID, "id_description")
    DOCUMENTS_INPUT = (By.ID, "id_documents")
    COMPLETE_SUBMIT = (
        By.CSS_SELECTOR,
        "button[type='submit'][name='submit_action'][value='complete']",
    )
    PAGE_TITLE = (By.TAG_NAME, "h4")
    ALERTS = (By.CSS_SELECTOR, ".alert")
    FIELD_ERRORS = (By.CSS_SELECTOR, ".text-danger.small")

    def go_to_case_create(self):
        self.driver.get(f"{BASE_URL}/casos/registrar/")
        self.find_element(self.PAGE_TITLE)

    def select_sala(self, sala_value):
        Select(self.find_element(self.SALA_SELECT)).select_by_value(sala_value)

    def select_beneficiary_by_text(self, beneficiary_name):
        Select(self.find_element(self.BENEFICIARY_SELECT)).select_by_visible_text(
            beneficiary_name
        )

    def fill_description(self, description):
        element = self.find_element(self.DESCRIPTION_TEXTAREA)
        element.clear()
        element.send_keys(description)

    def upload_document(self, file_path):
        absolute_path = os.path.abspath(file_path)
        self.find_element(self.DOCUMENTS_INPUT).send_keys(absolute_path)

    def submit_complete(self):
        previous_url = self.driver.current_url
        button = self.find_element(self.COMPLETE_SUBMIT)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", button
        )
        self.driver.execute_script("arguments[0].click();", button)
        WebDriverWait(self.driver, self.timeout).until(
            lambda d: d.current_url != previous_url or self.has_validation_feedback()
        )

    def submit_complete_with_native_click(self):
        button = self.find_element(self.COMPLETE_SUBMIT)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", button
        )
        button.send_keys(Keys.ENTER)
        WebDriverWait(self.driver, self.timeout).until(
            lambda d: self.has_validation_feedback()
            or self.get_active_validation_message()
            or d.current_url != f"{BASE_URL}/casos/registrar/"
        )

    def has_validation_feedback(self):
        return bool(
            self.driver.find_elements(*self.ALERTS)
            or self.driver.find_elements(*self.FIELD_ERRORS)
        )

    def current_url_is_case_detail(self):
        return bool(re.search(r"/casos/\d+/?$", self.driver.current_url))

    def get_page_text(self):
        def _read_body_text(driver):
            try:
                return driver.find_element(By.TAG_NAME, "body").text
            except StaleElementReferenceException:
                return False

        return WebDriverWait(self.driver, self.timeout).until(_read_body_text)

    def get_native_validation_message(self, field_locator):
        field = self.find_element(field_locator)
        return self.driver.execute_script(
            "return arguments[0].validationMessage;", field
        )

    def get_active_validation_message(self):
        return self.driver.execute_script(
            "return document.activeElement ? document.activeElement.validationMessage : '';"
        )

    def get_active_element_id(self):
        return self.driver.execute_script(
            "return document.activeElement ? document.activeElement.id : null;"
        )

    def form_is_valid(self):
        return self.driver.execute_script(
            "const form = document.querySelector('form'); return form ? form.checkValidity() : true;"
        )
