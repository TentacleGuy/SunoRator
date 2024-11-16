from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.settings_manager import settings_manager


class BrowserManager:
    def __init__(self):
        self.driver = None
        self.init_driver()

    def init_driver(self):
        chrome_options = Options()
        settings = settings_manager.get_settings()
        if settings.get('scraper', {}).get('headless', True):
            chrome_options.add_argument("--headless")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def get_driver(self):
        if not self.driver:
            self.init_driver()
        return self.driver

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None


browser_manager = BrowserManager()
