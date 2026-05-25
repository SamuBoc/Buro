from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage, BASE_URL


class DataDeletionPage(BasePage):
    REQUEST_BUTTON = (
        By.CSS_SELECTOR,
        "a.btn.btn-outline-danger[href*='solicitar-eliminacion']",
    )
    REASON_TEXTAREA = (By.ID, "id_reason")
    CONFIRM_CHECKBOX = (By.ID, "id_confirm_request")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit'].btn-danger")
    PAGE_HEADER = (By.TAG_NAME, "h4")

    def go_to_beneficiary_detail(self, beneficiary_id):
        self.driver.get(f"{BASE_URL}/beneficiarios/beneficiario/{beneficiary_id}/")
        self.find_element(self.PAGE_HEADER)

    def click_request_deletion(self):
        self.click(self.REQUEST_BUTTON)

    def fill_reason(self, reason):
        field = self.find_element(self.REASON_TEXTAREA)
        field.clear()
        field.send_keys(reason)

    def confirm_request(self):
        checkbox = self.find_element(self.CONFIRM_CHECKBOX)
        if not checkbox.is_selected():
            self.driver.execute_script("arguments[0].click();", checkbox)

    def submit_request(self):
        previous_url = self.driver.current_url
        button = self.find_element(self.SUBMIT_BUTTON)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", button
        )
        self.driver.execute_script("arguments[0].form.requestSubmit(arguments[0]);", button)
        WebDriverWait(self.driver, self.timeout).until(
            lambda d: d.current_url != previous_url or "solicitud" in self.get_page_text().lower()
        )

    def go_to_request_list(self):
        self.driver.get(f"{BASE_URL}/beneficiarios/solicitudes-eliminacion/")
        self.find_element(self.PAGE_HEADER)

    def get_page_text(self):
        return self.driver.find_element(By.TAG_NAME, "body").text
