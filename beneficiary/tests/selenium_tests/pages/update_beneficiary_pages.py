from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from .base_page import BasePage

import time

class RegisterBeneficiarySelenium(BasePage) :
    BENEFICIARY_MODULE = (By.CLASS_NAME, "beneficiary-module")

    ACTIONS_BENEFICIARY = (By.ID, "actions-user")

    GO_TO_UPDATE = (By.ID, "do-update")

    MODIFY_LOCATION = (By.ID, "id_location")

    MODIFY_PHONE = (By.ID, "id_phone")

    BUTTON_SUBMIT = (By.ID, "update-beneficiary")

    GO_TO_BINNACLE = (By.ID, "binnacle-beneficiary")

    def go_to_homepage(self, url = "http://127.0.0.1:8000/"):
        self.driver.get(url)

    def go_to_beneficiary_module(self):
        self.click(self.BENEFICIARY_MODULE)

    def beneficiary_details(self):
        self.click(self.ACTIONS_BENEFICIARY)

    def go_to_update(self):
        self.click(self.GO_TO_UPDATE)

    def modify_some_fields(self):
        self.enter_text(self.MODIFY_LOCATION, "Ciudad Pesadilla, ICESI")
        self.enter_text(self.MODIFY_PHONE, "911")
        
    def make_update(self):
        self.click(self.BUTTON_SUBMIT)

    def go_to_binnacle(self):
        self.click(self.GO_TO_BINNACLE)