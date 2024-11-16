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
        print("Starting browser initialization...")
        chrome_options = Options()
        settings = settings_manager.get_settings()
        print(f"Got settings: {settings}")
        scraper_settings = settings.get('scraper', {})
        print(f"Scraper settings: {scraper_settings}")

        if scraper_settings.get('headless', True):
            chrome_options.add_argument("--headless")
        if scraper_settings.get('no_sandbox', True):
            chrome_options.add_argument("--no-sandbox")
        if scraper_settings.get('dev_shm_usage', True):
            chrome_options.add_argument("--disable-dev-shm-usage")

        window_size = scraper_settings.get('window_size', '1920,1080')
        chrome_options.add_argument(f"--window-size={window_size}")

        print("Creating Chrome driver...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome driver created successfully")

    def get_driver(self):
        if not self.driver:
            self.init_driver()
        return self.driver

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None


browser_manager = BrowserManager()
