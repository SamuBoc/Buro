from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select

from .base_page import BasePage


class HU15ScheduleCitePage(BasePage):
    MODALITY_FIELD = (By.ID, 'id_modality_cite')
    REQUEST_FIELD = (By.ID, 'id_request_cite')
    DATE_FIELD = (By.ID, 'id_date_assigned')
    DESCRIPTION_FIELD = (By.ID, 'id_description')
    SUBMIT_BUTTON = (By.ID, 'submit-cite-form')
    MODALITY_ERROR = (By.XPATH, "//*[contains(., 'Debes seleccionar una modalidad valida para continuar.')]")
    CITE_LIST_TABLE = (By.XPATH, "//table[@class='table table-hover align-middle mb-0']")
    FIRST_MODALITY_CELL = (By.XPATH, "//table//tbody/tr[1]/td[2]")
    FIRST_DESCRIPTION_CELL = (By.XPATH, "//table//tbody/tr[1]/td[6]")

    def go_to_login(self, base_url):
        self.driver.get(f'{base_url}/login/')

    def go_to_beneficiary_detail(self, base_url, beneficiary_id):
        self.driver.get(f'{base_url}/beneficiarios/beneficiario/{beneficiary_id}/')

    def wait_for_beneficiary_detail(self, beneficiary_id):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: f'/beneficiarios/beneficiario/{beneficiary_id}/' in driver.current_url
        )

    def go_to_cite_form(self, base_url, beneficiary_id):
        self.driver.get(f'{base_url}/citas/beneficiario/{beneficiary_id}/agendar/')

    def open_cite_form_from_detail(self):
        self.click((By.ID, 'new-cite'))

    def wait_for_cite_form(self):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: driver.find_elements(*self.MODALITY_FIELD)
        )

    def wait_for_cite_list(self):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: driver.find_elements(By.XPATH, "//table//tbody/tr")
        )

    def go_to_cite_list(self, base_url, beneficiary_id):
        self.driver.get(f'{base_url}/citas/beneficiario/{beneficiary_id}/')

    def select_modality(self, modality_value):
        select = Select(self.find_element(self.MODALITY_FIELD))
        select.select_by_value(modality_value)

    def clear_modality(self):
        field = self.find_element(self.MODALITY_FIELD)
        self.driver.execute_script(
            """
            const select = arguments[0];
            select.selectedIndex = -1;
            select.dispatchEvent(new Event('change', { bubbles: true }));
            """,
            field,
        )

    def select_request(self, request_value='Página Web'):
        select = Select(self.find_element(self.REQUEST_FIELD))
        select.select_by_visible_text(request_value)

    def fill_date(self, date_value):
        field = self.find_element(self.DATE_FIELD)
        self.driver.execute_script(
            """
            const input = arguments[0];
            const value = arguments[1];
            input.value = value;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            """,
            field,
            date_value,
        )

    def fill_description(self, description_text):
        field = self.find_element(self.DESCRIPTION_FIELD)
        field.clear()
        field.send_keys(description_text)

    def submit(self):
        button = self.find_element(self.SUBMIT_BUTTON)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            button,
        )
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable(self.SUBMIT_BUTTON)
            ).click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", button)

    def wait_for_success_redirect(self, beneficiary_id):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: f'/beneficiarios/beneficiario/{beneficiary_id}/' in driver.current_url
        )

    def error_visible(self):
        return self.find_element(self.MODALITY_ERROR).text.strip()

    def wait_for_error_message(self):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: driver.find_elements(*self.MODALITY_ERROR)
        )

    def cite_list_modalities(self):
        return self.find_element(self.CITE_LIST_TABLE)

    def first_modality_text(self):
        return self.find_element(self.FIRST_MODALITY_CELL).text.strip()

    def first_description_text(self):
        return self.find_element(self.FIRST_DESCRIPTION_CELL).text.strip()

    def current_url_contains(self, text):
        return text in self.driver.current_url
