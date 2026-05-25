"""
Important!! Selenium test will fail because user is in the local Database.
Please adjust the user and password in base how you create the user.
"""
from selenium.webdriver.common.by import By
from .base_page import BasePage


class LoginPage(BasePage):
    USER_INPUT = (By.ID, 'id_username')
    PASSWORD_INPUT = (By.ID, 'id_password')
    BUTTON_SUBMIT = (By.CLASS_NAME, 'btn-submit')

    def go_to_homepage(self, url='http://127.0.0.1:8000/login/'):
        self.driver.get(url)

    def make_log_in(self, user='stevan', password='useruser'):
        self.enter_text(self.USER_INPUT, user)
        self.enter_text(self.PASSWORD_INPUT, password)
        self.click(self.BUTTON_SUBMIT)
