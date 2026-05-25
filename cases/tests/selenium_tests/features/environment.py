import os
import subprocess
import sys
import time
import urllib.request
import django
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Add Django project root to path and set up ORM for test data creation
_SELENIUM_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, _SELENIUM_ROOT)
sys.path.insert(0, _PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth.models import User, Group

_BASE_URL = "http://127.0.0.1:8000"


def _ensure_user(username, password, group_name):
    """Create or update a user with exactly one group."""
    group, _ = Group.objects.get_or_create(name=group_name)
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.save()
    user.groups.set([group])
    return user


def _is_server_available():
    try:
        with urllib.request.urlopen(f"{_BASE_URL}/login/", timeout=2) as response:
            return response.status < 500
    except Exception:
        return False


def _start_test_server():
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    process = subprocess.Popen(
        [
            sys.executable,
            "manage.py",
            "runserver",
            "127.0.0.1:8000",
            "--noreload",
        ],
        cwd=_PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )

    timeout_at = time.time() + 30
    while time.time() < timeout_at:
        if _is_server_available():
            return process
        if process.poll() is not None:
            break
        time.sleep(1)

    process.terminate()
    raise RuntimeError(
        "No fue posible iniciar el servidor Django para las pruebas Selenium en "
        f"{_BASE_URL}."
    )


def before_all(context):
    """Ensure test users exist and locate recording test data."""
    from cases.models import CommunicationInteraction
    from beneficiary.models import Beneficiary

    _ensure_user('admin_selenium', 'selenium123', 'administrador')
    _ensure_user('secretaria_selenium', 'selenium123', 'secretaria')

    selenium_beneficiary = Beneficiary.objects.filter(
        email='beneficiario.selenium.hu6@test.com'
    ).first()
    if selenium_beneficiary is None:
        selenium_beneficiary = Beneficiary.objects.create(
            name='Beneficiario Selenium HU6',
            email='beneficiario.selenium.hu6@test.com',
            phone='3001234567',
            colombian_identification='1234567890',
        )
    context.selenium_beneficiary = selenium_beneficiary

    # Find the first interaction with an actual audio_file in the DB.
    # These tests rely on existing data; they cannot run on a completely empty DB.
    interaction = (
        CommunicationInteraction.objects
        .filter(audio_file__isnull=False)
        .exclude(audio_file='')
        .order_by('pk')
        .first()
    )

    if interaction:
        context.selenium_case_id = interaction.case_id
        context.selenium_interaction_id = interaction.pk
    else:
        context.selenium_case_id = None
        context.selenium_interaction_id = None

    context.started_test_server = False
    context.server_process = None
    if not _is_server_available():
        context.server_process = _start_test_server()
        context.started_test_server = True


def before_scenario(context, scenario):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1440,1600')
    context.driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def after_scenario(context, scenario):
    context.driver.quit()


def after_all(context):
    process = getattr(context, "server_process", None)
    if getattr(context, "started_test_server", False) and process is not None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
