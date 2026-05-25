from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from .base_page import BasePage

class RescheduleCite(BasePage):
    BENEFICIARY_MODULE = (By.CLASS_NAME, "beneficiary-module")

    ACTIONS_USER = (By.ID, "actions-user")

    CITE_MODULE = (By.ID, "see-cites")

    BUTTON_RESCHEDULE = (By.CLASS_NAME, "reschedule-cite")

    DATE_INPUT = (By.ID, "id_date_assigned")

    SUBMIT_RESCHEDULE = (By.ID, "reschedule-submit")

    DATE_FIELD = (By.ID, "assigment-date")

    def go_to_homepage(self, url = "http://127.0.0.1:8000/"):
        self.driver.get(url)

    def go_to_beneficiary_module(self):
        self.click(self.BENEFICIARY_MODULE)

    def go_to_actions_user(self):
        self.click(self.ACTIONS_USER)

    def go_to_cite_module(self):
        self.click(self.CITE_MODULE)

    def reschedule_cite(self):
        self.click(self.BUTTON_RESCHEDULE)


    # I have the same trouble in schedule:cite_page. Selenium just skip the last instructions about field.send_keys(Keys.ARROW_DOWN)
    # And this make test can't continue, I use time you can see beter the trouble, I tryed to use other things but don't work
    def new_date(self):
        field = self.find_element(self.DATE_INPUT)
        field.send_keys("01012050")  
        time.sleep(2)
        field.send_keys(Keys.TAB)    
        time.sleep(2)
        field.send_keys("0100") 
        time.sleep(2)     
        field.send_keys(Keys.TAB)
        time.sleep(2)    
        field.send_keys(Keys.ARROW_DOWN)
        self.click(self.SUBMIT_RESCHEDULE)

    def get_actual_date(self):
        date = self.find_element(self.DATE_FIELD)
        return date.text