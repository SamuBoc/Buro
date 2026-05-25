from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from .base_page import BasePage

import time

class UpdateBeneficiarySelenium(BasePage) :
    BENEFICIARY_MODULE = (By.CLASS_NAME, "beneficiary-module")

    ACTIONS_BENEFICIARY = (By.ID, "actions-user")

    GO_TO_UPDATE = (By.ID, "do-update")

    MODIFY_LOCATION = (By.ID, "id_location")

    MODIFY_PHONE = (By.ID, "id_phone")

    BUTTON_SUBMIT = (By.ID, "update-beneficiary")

    LOCATION_FIELD = (By.ID, "location-beneficiary")

    PHONE_FIELD = (By.ID, "phone-beneficiary")

    GO_TO_BINNACLE = (By.ID, "binnacle-beneficiary")

    ACTION_DONE = (By.ID, "description-action-UPDATED-2")

    # Cancel Modifications
    CANCEL_BUTTON = (By.ID, "cancel-update")

    MODIFY_NAME = (By.ID, "id_name")

    FIELD_NAME = (By.ID, "name-beneficiary")

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

    def get_location_modified(self):
        location = self.find_element(self.LOCATION_FIELD)
        return location.text

    def get_phone_modified(self):
        phone = self.find_element(self.PHONE_FIELD)
        return phone.text

    def go_to_binnacle(self):
        self.click(self.GO_TO_BINNACLE)

    def get_action_done(self):
        action = self.find_element(self.ACTION_DONE)
        return action.text
    
    def modify_some_fields_to_cancel(self):
        self.enter_text(self.MODIFY_NAME, "No soy real")

    def cancel_update(self):
        self.click(self.CANCEL_BUTTON)

    def get_name(self):
        name = self.find_element(self.FIELD_NAME)
        return name.text