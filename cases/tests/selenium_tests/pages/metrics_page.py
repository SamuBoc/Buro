from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from .base_page import BasePage, BASE_URL


class MetricsPage(BasePage):
    METRIC_CARDS = (By.CSS_SELECTOR, '.card .fw-bold')
    FILTER_SELECT = (By.NAME, 'tipo')
    FILTER_BUTTON = (By.CSS_SELECTOR, 'button[type="submit"]')
    CLEAR_BUTTON = (By.PARTIAL_LINK_TEXT, 'Limpiar')
    TABLE_ROWS = (By.CSS_SELECTOR, 'tbody tr')
    CHANNEL_BADGES = (By.CSS_SELECTOR, 'tbody .badge.bg-secondary')

    def go_to_metrics(self):
        self.driver.get(f"{BASE_URL}/casos/metricas/comunicaciones/")

    def get_metric_counts(self):
        elements = self.find_elements(self.METRIC_CARDS)
        return [e.text for e in elements]

    def filter_by_type(self, tipo_value):
        select = Select(self.find_element(self.FILTER_SELECT))
        select.select_by_value(tipo_value)
        self.click(self.FILTER_BUTTON)

    def clear_filter(self):
        self.click(self.CLEAR_BUTTON)

    def get_table_row_count(self):
        rows = self.driver.find_elements(*self.TABLE_ROWS)
        if rows and 'No hay interacciones' in rows[0].text:
            return 0
        return len(rows)

    def get_visible_channel_labels(self):
        badges = self.driver.find_elements(*self.CHANNEL_BADGES)
        return [b.text for b in badges]

    def get_current_url(self):
        return self.driver.current_url
