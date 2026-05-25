from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from .base_page import BasePage

import time

class RegisterBeneficiarySelenium(BasePage) :
    BENEFICIARY_MODULE = (By.CLASS_NAME, "beneficiary-module")

    GO_TO_REGISTER = (By.ID, "register-beneficiary")

    FIELD_NAME = (By.ID, "id_name")

    FIELD_ID = (By.ID, "id_colombian_identification")

    FIELD_LOCATION = (By.ID, "id_location")

    FIELD_PHONE = (By.ID, "id_phone")

    FIELD_MAIL = (By.ID, "id_email")

    FIELD_CONDITIONS = (By.ID, "id_allow_conditions")

    BUTTON_SAVE = (By.ID, "save-beneficiary")

    BENEFICIARY_NAME = (By.ID, "name-beneficiary-1")

    EMPTY_CASE = (By.CLASS_NAME, "cant-be-empty")

    def go_to_homepage(self, url = "http://127.0.0.1:8000/"):
        self.driver.get(url)

    def go_to_beneficiary_module(self):
        self.click(self.BENEFICIARY_MODULE)

    def go_to_register(self):
        self.click(self.GO_TO_REGISTER)

    def complete_fields(self):
        self.enter_text(self.FIELD_NAME, "Usuario de prueba selenium")
        self.enter_text(self.FIELD_ID, "123456789")
        self.enter_text(self.FIELD_LOCATION, "Pais de la felicidad, Imaginario")
        self.enter_text(self.FIELD_PHONE, "123456789")
        self.enter_text(self.FIELD_MAIL, "soyuncorreo@gmail.com")
        self.click(self.FIELD_CONDITIONS)
        print('Please you need to upload at file from your pc. Its only for this selenium test please')
        time.sleep(10)
        
    def make_register(self):
        self.click(self.BUTTON_SAVE)

    def get_data(self):
        name_beneficiary = self.find_element(self.BENEFICIARY_NAME)
        return name_beneficiary.text
    
    #This is for the other scenario of HU-1
    def incomplete_fields(self):
        self.enter_text(self.FIELD_NAME, "Usuario de prueba selenium")
        self.enter_text(self.FIELD_ID, "123456789")
        self.enter_text(self.FIELD_LOCATION, "Pais de la felicidad, Imaginario")
        self.enter_text(self.FIELD_PHONE, "123456789")
        self.enter_text(self.FIELD_MAIL, "soyuncorreo@gmail.com")
        self.click(self.FIELD_CONDITIONS)

    def get_empty_alert(self):
        alert = self.find_element(self.EMPTY_CASE)
        return alert.text
    
    def dont_mark_authorization(self):
        self.enter_text(self.FIELD_NAME, "Usuario de prueba selenium")
        self.enter_text(self.FIELD_ID, "123456789")
        self.enter_text(self.FIELD_LOCATION, "Pais de la felicidad, Imaginario")
        self.enter_text(self.FIELD_PHONE, "123456789")
        self.enter_text(self.FIELD_MAIL, "soyuncorreo@gmail.com")
        print('Please you need to upload at file from your pc. Its only for this selenium test please')
        time.sleep(10)

    
