from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

BASE_URL = "http://127.0.0.1:8000"

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 20

    def find_element(self, locator):
        return WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located(locator)
        )

    def find_elements(self, locator):
        return WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_all_elements_located(locator)
        )

    def click(self, locator):
        element = WebDriverWait(self.driver, self.timeout).until(
            EC.element_to_be_clickable(locator)
        )
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        element.click()

    def enter_text(self, locator, text):
        self.find_element(locator).send_keys(text)

    def get_text(self, locator):
        return self.find_element(locator).text

    def is_element_present(self, locator):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except Exception:
            return False 