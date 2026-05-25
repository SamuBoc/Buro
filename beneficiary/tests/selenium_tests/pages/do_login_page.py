from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from .base_page import BasePage

from accounts.constants import ROLE_ADMINISTRADOR
from django.contrib.auth.models import Group, User

import time

class LoginPage(BasePage):
    USER_INPUT = (By.ID, 'id_username')

    PASSWORD_INPUT = (By.ID, 'id_password')

    BUTTON_SUBMIT = (By.CLASS_NAME, 'btn-submit')

    def make_user(self, username='Admin', password='pass1234', group_name=ROLE_ADMINISTRADOR):
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.email = f'{username}@test.com'
            user.save()
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
        return user

    def go_to_homepage(self, url = "http://127.0.0.1:8000/login/"):
        self.driver.get(url)
        

    def make_log_in(self):
        self.make_user('Admin', 'pass1234')
        username = "Admin"
        password = 'pass1234'
        self.enter_text(self.USER_INPUT, username)
        self.enter_text(self.PASSWORD_INPUT, password)
        self.click(self.BUTTON_SUBMIT)


