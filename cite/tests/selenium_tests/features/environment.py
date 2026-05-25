import sys
import os
import django

# It's your responsability download and put in selenium_tests/ the file chromedriver.exe for the right execute of selenium tests :D
# Raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')))

# selenium_tests/ para encontrar la carpeta 'pages'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from selenium import webdriver

def before_scenario(context, scenario):
    context.driver = webdriver.Chrome()
    context.driver.maximize_window()

def after_scenario(context, scenario):
    from django.contrib.auth.models import User
    User.objects.filter(username='Admin').delete()
    context.driver.quit()