from selenium.webdriver.common.by import By

from .base_page import BasePage


class AcademicDashboardPage(BasePage):
    PANEL_CONTAINER = (By.ID, 'academic-dashboard')
    METRICS_CONTAINER = (By.ID, 'academic-metrics')
    STUDENTS_TABLE = (By.ID, 'academic-students-table')
    DETAIL_LINKS = (By.CSS_SELECTOR, '.academic-detail-link')
    EMPTY_STATE = (By.ID, 'academic-empty-state')

    STUDENT_DETAIL_CONTAINER = (By.ID, 'academic-student-detail')
    STUDENT_METRICS = (By.ID, 'academic-student-metrics')
    STUDENT_CASES_TABLE = (By.ID, 'academic-student-cases-table')
    STUDENT_EMPTY_STATE = (By.ID, 'academic-student-empty-state')

    def go_to_panel(self, base_url):
        self.driver.get(f"{base_url}/casos/panel-academico/")

    def wait_for_panel(self):
        return self.find_element(self.PANEL_CONTAINER)

    def metrics_visible(self):
        return self.find_element(self.METRICS_CONTAINER)

    def has_students(self):
        try:
            table = self.find_element(self.STUDENTS_TABLE)
            rows = table.find_elements(By.CSS_SELECTOR, 'tbody tr')
            return len(rows) > 0
        except Exception:
            return False

    def open_first_student_detail(self):
        links = self.driver.find_elements(*self.DETAIL_LINKS)
        if not links:
            return False
        links[0].click()
        return True

    def wait_for_student_detail(self):
        return self.find_element(self.STUDENT_DETAIL_CONTAINER)

    def student_metrics_visible(self):
        return self.find_element(self.STUDENT_METRICS)

    def student_cases_visible(self):
        try:
            table = self.find_element(self.STUDENT_CASES_TABLE)
            rows = table.find_elements(By.CSS_SELECTOR, 'tbody tr')
            return len(rows) > 0
        except Exception:
            return False

    def student_empty_state_visible(self):
        try:
            self.find_element(self.STUDENT_EMPTY_STATE)
            return True
        except Exception:
            return False
