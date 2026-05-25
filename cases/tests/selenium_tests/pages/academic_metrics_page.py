from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base_page import BasePage, BASE_URL


class AcademicMetricsPage(BasePage):
    PAGE_HEADER = (By.TAG_NAME, "h2")
    STUDENT_FILTER = (By.ID, "estudiante")
    SALA_FILTER = (By.ID, "sala")
    FILTER_BUTTON = (By.CSS_SELECTOR, "form[method='get'] button[type='submit']")
    TABLE_ROWS = (By.CSS_SELECTOR, "table tbody tr")

    def go_to_dashboard(self):
        self.driver.get(f"{BASE_URL}/casos/panel-academico/")
        self.find_element(self.PAGE_HEADER)

    def go_to_student_detail(self, student_id):
        self.driver.get(f"{BASE_URL}/casos/panel-academico/estudiante/{student_id}/")
        self.find_element(self.PAGE_HEADER)

    def filter_by_student_and_sala(self, student_visible_text=None, sala_value=None):
        if student_visible_text:
            Select(self.find_element(self.STUDENT_FILTER)).select_by_visible_text(
                student_visible_text
            )
        if sala_value:
            Select(self.find_element(self.SALA_FILTER)).select_by_value(sala_value)

        previous_url = self.driver.current_url
        self.click(self.FILTER_BUTTON)
        WebDriverWait(self.driver, self.timeout).until(
            lambda d: d.current_url != previous_url
        )

    def get_page_text(self):
        return self.driver.find_element(By.TAG_NAME, "body").text

    def get_table_rows_text(self):
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        return [row.text for row in rows]
