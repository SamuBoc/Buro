from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage

class CancelCite(BasePage):
    BENEFICIARY_MODULE = (By.CLASS_NAME, "beneficiary-module")

    ACTIONS_USER = (By.ID, "actions-user")

    CITE_MODULE = (By.ID, "see-cites")

    CANCEL_BUTTON = (By.ID, "cancel-cite")

    CANCEL_AGREE_BUTTON = (By.ID, "actionConfirmSubmit")

    STATE_FIELD = (By.ID, "actual-state-1")

    def go_to_homepage(self, url = "http://127.0.0.1:8000/"):
        self.driver.get(url)

    def go_to_beneficiary_module(self):
        self.click(self.BENEFICIARY_MODULE)

    def go_to_actions_user(self):
        self.click(self.ACTIONS_USER)

    def go_to_cite_module(self):
        self.click(self.CITE_MODULE)

    def cancel_cite(self):
        self.click(self.CANCEL_BUTTON)
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable(self.CANCEL_AGREE_BUTTON)
        ).click()

    def get_state_cite(self):
        state = WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located(self.STATE_FIELD)
        )
        return state.text
