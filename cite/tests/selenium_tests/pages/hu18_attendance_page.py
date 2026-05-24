from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class HU18AttendancePage(BasePage):
    ATTENDANCE_MODAL_BUTTON = (By.ID, 'actionConfirmSubmit')

    def go_to_beneficiary_cites(self, base_url, beneficiary_id):
        self.driver.get(f'{base_url}/citas/beneficiario/{beneficiary_id}/')

    def wait_for_cite_list(self):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: driver.find_elements(By.XPATH, "//table//tbody/tr")
        )

    def _row_locator(self, cite_id):
        return (By.XPATH, f"//tr[td[normalize-space()='{cite_id}']]")

    def _attendance_button_locator(self, cite_id, status):
        return (
            By.XPATH,
            f"//tr[td[normalize-space()='{cite_id}']]//form[contains(@action, '/asistencia/{status}/')]//button",
        )

    def _state_locator(self, cite_id):
        return (
            By.XPATH,
            f"//tr[td[normalize-space()='{cite_id}']]//span[contains(@id, 'actual-state-')]",
        )

    def register_attendance(self, cite_id, status):
        self.click(self._attendance_button_locator(cite_id, status))
        WebDriverWait(self.driver, self.timeout).until(
            EC.element_to_be_clickable(self.ATTENDANCE_MODAL_BUTTON)
        ).click()

    def state_text(self, cite_id):
        return self.find_element(self._state_locator(cite_id)).text.strip()
