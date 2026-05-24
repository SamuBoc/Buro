from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.timeout = 20

    def find_element(self, locator):
        return WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located(locator)
        )

    def click(self, locator):
        self.find_element(locator).click()

    def scroll_into_view(self, locator):
        element = self.find_element(locator)
        self.driver.execute_script('arguments[0].scrollIntoView({block: "center"});', element)
        return element

    def click_js(self, locator):
        element = self.scroll_into_view(locator)
        self.driver.execute_script('arguments[0].click();', element)

    def enter_text(self, locator, text):
        self.find_element(locator).send_keys(text)
