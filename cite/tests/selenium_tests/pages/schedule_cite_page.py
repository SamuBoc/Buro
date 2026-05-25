from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from .base_page import BasePage

class ScheduleCite(BasePage) :
    BENEFICIARY_MODULE = (By.CLASS_NAME, "beneficiary-module")

    ACTIONS_USER = (By.ID, "actions-user")

    NEW_CITE = (By.ID, "new-cite")

    DATE_FIELD = (By.ID, "id_date_assigned")
    DESCRIPTION_DATE = (By.ID, "id_description")

    SUBMIT_BUTTON = (By.ID, "submit-cite-form")

    CITE_MODULE = (By.ID, "see-cites")

    DATE_ASSIGMENT = (By.ID, "assigment-date")

    def go_to_homepage(self, url = "http://127.0.0.1:8000/"):
        self.driver.get(url)

    def go_to_beneficiary_module(self):
        self.click(self.BENEFICIARY_MODULE)

    def go_to_actions_user(self):
        self.click(self.ACTIONS_USER)

    def go_to_cite_form(self):
        self.click(self.NEW_CITE)

    def define_date_cite(self):
        field = self.find_element(self.DATE_FIELD)
        field.send_keys("01012040")  
        field.send_keys(Keys.TAB)    
        field.send_keys("0100")      
        field.send_keys(Keys.TAB)    
        field.send_keys("p")         
        self.enter_text(self.DESCRIPTION_DATE, "Prueba selenium")

    def send_form(self):
        self.click(self.SUBMIT_BUTTON)

    def go_to_cite_module(self):
        self.click(self.CITE_MODULE)

    def get_date_assigment(self):
        date_assigment = self.find_element(self.DATE_ASSIGMENT)
        return date_assigment.text

    
