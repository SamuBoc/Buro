import sqlite3
from pathlib import Path

from selenium.webdriver.common.by import By
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

    def _repo_root(self):
        return Path(__file__).resolve().parents[4]

    def _db_path(self):
        return self._repo_root() / 'db.sqlite3'

    def _get_first_beneficiary(self):
        with sqlite3.connect(self._db_path()) as connection:
            row = connection.execute(
                'SELECT id, name FROM beneficiary_beneficiary ORDER BY date_register DESC, id LIMIT 1'
            ).fetchone()
        if not row:
            return None, None
        return row[0], row[1]

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

    def go_to_cite_list(self, base_url, beneficiary_id):
        self.driver.get(f'{base_url}/citas/beneficiario/{beneficiary_id}/')

    def go_to_first_beneficiary_cite_list(self, base_url):
        beneficiary_id, _ = self._get_first_beneficiary()
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
        self.click(self.SUBMIT_BUTTON)

    def wait_for_success_redirect(self, beneficiary_id):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: f'/beneficiarios/beneficiario/{beneficiary_id}/' in driver.current_url
        )

    def wait_for_cite_saved(self, beneficiary_id, modality_value, description_text):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: self._cite_exists(beneficiary_id, modality_value, description_text)
        )

    def _cite_exists(self, beneficiary_id, modality_value, description_text):
        with sqlite3.connect(self._db_path()) as connection:
            row = connection.execute(
                '''
                SELECT 1
                FROM cite_cite
                WHERE beneficiary_id = ?
                  AND modality_cite = ?
                  AND description = ?
                LIMIT 1
                ''',
                (beneficiary_id, modality_value, description_text),
            ).fetchone()

        return row is not None

    def error_visible(self):
        return self.find_element(self.MODALITY_ERROR).text.strip()

    def cite_list_modalities(self):
        return self.find_element(self.CITE_LIST_TABLE)

    def first_modality_text(self):
        return self.find_element(self.FIRST_MODALITY_CELL).text.strip()

    def first_description_text(self):
        return self.find_element(self.FIRST_DESCRIPTION_CELL).text.strip()

    def current_url_contains(self, text):
        return text in self.driver.current_url
