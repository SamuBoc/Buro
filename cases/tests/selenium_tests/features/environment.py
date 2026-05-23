import os
import sys
import django
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Add Django project root to path and set up ORM for test data creation
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, _PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth.models import User, Group


def _ensure_user(username, password, group_name):
    """Create or update a user with exactly one group."""
    group, _ = Group.objects.get_or_create(name=group_name)
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.save()
    user.groups.set([group])
    return user


def before_all(context):
    """Ensure test users exist and locate recording test data."""
    from cases.models import CommunicationInteraction

    _ensure_user('admin_selenium', 'selenium123', 'administrador')
    _ensure_user('secretaria_selenium', 'selenium123', 'secretaria')

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


def before_scenario(context, scenario):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,900')
    context.driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )


def after_scenario(context, scenario):
    context.driver.quit()
