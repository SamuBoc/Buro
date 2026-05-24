import os
import sys
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

WINDOWS_BROWSER_PATHS = {
    'chrome': [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    ],
    'edge': [
        r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    ],
    'firefox': [
        r'C:\Program Files\Mozilla Firefox\firefox.exe',
        r'C:\Program Files (x86)\Mozilla Firefox\firefox.exe',
    ],
}


def _is_truthy(value, default='0'):
    return str(value if value is not None else default).strip().lower() in {
        '1', 'true', 'yes', 'on',
    }


def _find_cached_driver(browser_name):
    if browser_name != 'chrome':
        return None

    cache_root = Path.home() / '.cache' / 'selenium' / 'chromedriver'
    if not cache_root.exists():
        return None

    candidates = sorted(
        cache_root.rglob('chromedriver.exe'),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return str(candidates[0]) if candidates else None


def _common_options(options, browser_name):
    if _is_truthy(os.getenv('SELENIUM_HEADLESS', '1')):
        if browser_name in {'chrome', 'edge'}:
            options.add_argument('--headless=new')
        else:
            options.add_argument('-headless')

    if browser_name in {'chrome', 'edge'}:
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

    binary = os.getenv('SELENIUM_BROWSER_BINARY')
    if not binary:
        for candidate in WINDOWS_BROWSER_PATHS.get(browser_name, []):
            if os.path.isfile(candidate):
                binary = candidate
                break
    if binary:
        options.binary_location = binary

    return options


def _build_chrome_driver():
    options = _common_options(ChromeOptions(), 'chrome')
    driver_path = os.getenv('SELENIUM_DRIVER_PATH') or _find_cached_driver('chrome')
    if driver_path:
        return webdriver.Chrome(service=ChromeService(driver_path), options=options)

    return webdriver.Chrome(options=options)


def _build_edge_driver():
    options = _common_options(EdgeOptions(), 'edge')
    driver_path = os.getenv('SELENIUM_DRIVER_PATH')
    if driver_path:
        return webdriver.Edge(service=EdgeService(driver_path), options=options)

    return webdriver.Edge(options=options)


def _build_firefox_driver():
    options = _common_options(FirefoxOptions(), 'firefox')
    driver_path = os.getenv('SELENIUM_DRIVER_PATH')
    if driver_path:
        return webdriver.Firefox(service=FirefoxService(driver_path), options=options)

    return webdriver.Firefox(options=options)


def _build_driver():
    browser = os.getenv('SELENIUM_BROWSER', 'chrome').strip().lower()
    builders = {
        'chrome': _build_chrome_driver,
        'edge': _build_edge_driver,
        'firefox': _build_firefox_driver,
    }

    if browser not in builders:
        raise ValueError(
            f"SELENIUM_BROWSER debe ser uno de {', '.join(sorted(builders))}. "
            f"Valor recibido: {browser!r}"
        )

    return builders[browser]()


def before_scenario(context, scenario):
    """
    Esta funcion se ejecuta antes de cada escenario de prueba.
    Inicializa el WebDriver y lo almacena en el contexto.
    """
    context.driver = _build_driver()
    context.driver.maximize_window()


def after_scenario(context, scenario):
    """
    Esta funcion se ejecuta despues de cada escenario de prueba.
    Cierra el navegador para limpiar despues de cada prueba.
    """
    driver = getattr(context, 'driver', None)
    if driver is not None:
        driver.quit()
