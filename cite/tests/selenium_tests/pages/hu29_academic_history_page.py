from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class HU29AcademicHistoryPage(BasePage):
    HISTORY_HEADER = (By.XPATH, "//h4[contains(., 'Historial academico')]")

    def go_to_history(self, base_url, student_id):
        self.driver.get(f'{base_url}/cuentas/estudiantes/{student_id}/historial/')

    def wait_for_history(self):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: driver.find_elements(*self.HISTORY_HEADER)
        )

    def _section_cell_locator(self, section_title, cell_text):
        return (
            By.XPATH,
            "//h5[contains(., '%s')]/ancestor::div[contains(@class, 'card')][1]"
            "//table//tbody//td[contains(normalize-space(), '%s')]"
            % (section_title, cell_text),
        )

    def case_visible_in_section(self, section_title, case_code):
        return bool(self.driver.find_elements(
            *self._section_cell_locator(section_title, case_code)
        ))

    def feedback_visible(self, feedback_text):
        return self.find_element(
            self._section_cell_locator('Retroalimentacion docente', feedback_text)
        ).text.strip()

    def text_visible(self, text):
        locator = (
            By.XPATH,
            "//*[contains(normalize-space(), '%s')]" % text,
        )
        return bool(self.driver.find_elements(*locator))
