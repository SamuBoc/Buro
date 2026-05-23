from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from .base_page import BasePage, BASE_URL


class LoginPage(BasePage):
    USER_INPUT = (By.ID, 'id_username')
    PASSWORD_INPUT = (By.ID, 'id_password')
    BUTTON_SUBMIT = (By.CLASS_NAME, 'btn-submit')

    def go_to_login(self):
        self.driver.get(f"{BASE_URL}/login/")

    def login(self, username, password):
        self.go_to_login()
        self.enter_text(self.USER_INPUT, username)
        self.enter_text(self.PASSWORD_INPUT, password)
        self.click(self.BUTTON_SUBMIT)
        # Wait until the browser leaves the login page (redirect completes)
        WebDriverWait(self.driver, 10).until(
            lambda d: '/login' not in d.current_url
        )
