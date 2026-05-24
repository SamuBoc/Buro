from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from .base_page import BasePage


class HU38AttendanceMetricsPage(BasePage):
    REPORT_TOTAL = (By.XPATH, "//span[contains(., 'Total registros:')]")
    ATTENDANCE_BADGE = (By.CSS_SELECTOR, 'span.badge.bg-success.me-2')
    NO_SHOW_BADGE = (By.CSS_SELECTOR, 'span.badge.bg-danger')
    REPORT_TABLE_ROWS = (By.CSS_SELECTOR, 'table tbody tr')

    def go_to_report(self, base_url):
        self.driver.get(f'{base_url}/citas/reportes/asistencia/')

    def wait_for_report(self):
        WebDriverWait(self.driver, self.timeout).until(
            lambda driver: driver.find_elements(*self.REPORT_TOTAL)
        )

    def total_text(self):
        return self.find_element(self.REPORT_TOTAL).text.strip()

    def attendance_badge_text(self):
        return self.find_element(self.ATTENDANCE_BADGE).text.strip()

    def no_show_badge_text(self):
        return self.find_element(self.NO_SHOW_BADGE).text.strip()

    def report_rows_count(self):
        return len(self.driver.find_elements(*self.REPORT_TABLE_ROWS))
