from selenium.webdriver.common.by import By

from .base_page import BasePage, BASE_URL


class RecordingAccessPage(BasePage):
    AUDIO_PLAYER = (By.CSS_SELECTOR, 'audio[controls]')
    LOCK_ICON = (By.CSS_SELECTOR, '.bi-lock-fill')
    INTERACTIONS_SECTION = (By.ID, 'interacciones')

    def go_to_case(self, case_id):
        self.driver.get(f"{BASE_URL}/casos/{case_id}/")

    def go_to_recording(self, interaction_id):
        self.driver.get(f"{BASE_URL}/casos/grabaciones/{interaction_id}/")

    def has_audio_player(self):
        return self.is_element_present(self.AUDIO_PLAYER)

    def has_lock_icon(self):
        return self.is_element_present(self.LOCK_ICON)

    def get_status_code_text(self):
        return self.driver.find_element(By.TAG_NAME, 'body').text

    def get_current_url(self):
        return self.driver.current_url
