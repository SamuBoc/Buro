"""
Requiere usuarios de prueba en la DB local:
  - admin_selenium / selenium123  (grupo: administrador)
  - secretaria_selenium / selenium123  (grupo: secretaria)

Crearlos con:
  python manage.py shell -c "
  from django.contrib.auth.models import User, Group
  for username, role in [('admin_selenium','administrador'),('secretaria_selenium','secretaria')]:
      u, _ = User.objects.get_or_create(username=username)
      u.set_password('selenium123'); u.save()
      g, _ = Group.objects.get_or_create(name=role)
      u.groups.set([g])
  "
"""
from selenium.webdriver.common.by import By
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
