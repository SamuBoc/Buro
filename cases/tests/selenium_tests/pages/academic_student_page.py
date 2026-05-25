from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

from .base_page import BasePage, BASE_URL


class AcademicStudentPage(BasePage):
    FIRST_NAME = (By.ID, "id_first_name")
    LAST_NAME = (By.ID, "id_last_name")
    EMAIL = (By.ID, "id_email")
    USERNAME = (By.ID, "id_username")
    STUDENT_CODE = (By.ID, "id_student_code")
    MAX_CASES = (By.ID, "id_max_cases")
    PREFERRED_ROOM = (By.ID, "id_preferred_room")
    SUPERVISING_PROFESSOR = (By.ID, "id_supervising_professor")
    PASSWORD = (By.ID, "id_password")
    AVAILABILITY = (By.ID, "id_availability")
    SUBMIT_BUTTON = (By.CSS_SELECTOR, "button[type='submit'].btn-primary")
    PAGE_HEADER = (By.TAG_NAME, "h4")

    def go_to_register(self):
        self.driver.get(f"{BASE_URL}/cuentas/estudiantes/registrar/")
        self.find_element(self.PAGE_HEADER)

    def go_to_list(self):
        self.driver.get(f"{BASE_URL}/cuentas/estudiantes/")
        self.find_element(self.PAGE_HEADER)

    def go_to_detail(self, student_id):
        self.driver.get(f"{BASE_URL}/cuentas/estudiantes/{student_id}/")
        self.find_element(self.PAGE_HEADER)

    def fill_registration_form(
        self,
        *,
        first_name,
        last_name,
        email,
        username,
        student_code,
        max_cases,
        preferred_room,
        password,
        availability=True,
        supervising_professor_visible_text=None,
    ):
        self.find_element(self.FIRST_NAME).clear()
        self.find_element(self.FIRST_NAME).send_keys(first_name)
        self.find_element(self.LAST_NAME).clear()
        self.find_element(self.LAST_NAME).send_keys(last_name)
        self.find_element(self.EMAIL).clear()
        self.find_element(self.EMAIL).send_keys(email)
        self.find_element(self.USERNAME).clear()
        self.find_element(self.USERNAME).send_keys(username)
        self.find_element(self.STUDENT_CODE).clear()
        self.find_element(self.STUDENT_CODE).send_keys(student_code)
        self.find_element(self.MAX_CASES).clear()
        self.find_element(self.MAX_CASES).send_keys(str(max_cases))
        Select(self.find_element(self.PREFERRED_ROOM)).select_by_value(preferred_room)
        if supervising_professor_visible_text:
            Select(self.find_element(self.SUPERVISING_PROFESSOR)).select_by_visible_text(
                supervising_professor_visible_text
            )
        self.find_element(self.PASSWORD).clear()
        self.find_element(self.PASSWORD).send_keys(password)

        checkbox = self.find_element(self.AVAILABILITY)
        if checkbox.is_selected() != availability:
            self.driver.execute_script("arguments[0].click();", checkbox)

    def submit_registration(self):
        previous_url = self.driver.current_url
        button = self.find_element(self.SUBMIT_BUTTON)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", button
        )
        self.driver.execute_script("arguments[0].form.requestSubmit(arguments[0]);", button)
        WebDriverWait(self.driver, self.timeout).until(
            lambda d: d.current_url != previous_url or "estudiante" in self.get_page_text().lower()
        )

    def get_page_text(self):
        return self.driver.find_element(By.TAG_NAME, "body").text
