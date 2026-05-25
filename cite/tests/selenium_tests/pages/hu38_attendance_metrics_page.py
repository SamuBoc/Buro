from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class HU38AttendanceMetricsPage(BasePage):
    REPORT_TOTAL = (By.XPATH, "//span[contains(., 'Total registros:')]")
    REPORT_TABLE_ROWS = (By.CSS_SELECTOR, 'table tbody tr')

    def go_to_report(self, base_url):
        self.driver.get(f'{base_url}/citas/reportes/asistencia/')

    def wait_for_report(self):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: driver.find_elements(*self.REPORT_TOTAL)
        )

    def total_text(self):
        return self.find_element(self.REPORT_TOTAL).text.strip()

    def report_rows_count(self):
        return len(self.driver.find_elements(*self.REPORT_TABLE_ROWS))

    def _row_cell_text(self, state_label, cell_index):
        locator = (
            By.XPATH,
            "//table//tbody/tr[td[normalize-space()='%s']]/td[%d]" % (state_label, cell_index),
        )
        return self.find_element(locator).text.strip()

    def row_count_text(self, state_label):
        return self._row_cell_text(state_label, 2)

    def row_percentage_text(self, state_label):
        return self._row_cell_text(state_label, 3)
