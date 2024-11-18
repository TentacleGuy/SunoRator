from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from utils.settings_manager import settings_manager
from config.vars import USERDATA_DIR
import os

class BrowserManager:
    def __init__(self):
        self.driver = None

    def init_driver(self):
        # Clean up any existing Chrome processes
        os.system("pkill -f 'Google Chrome'")

        print("Starting browser initialization...")
        chrome_options = Options()
        # User data directory with absolute path
        os.makedirs(USERDATA_DIR, exist_ok=True)
        chrome_options.add_argument(f"user-data-dir={USERDATA_DIR}")

        browser_settings = settings_manager.get_settings('browser')

        # Get nested settings
        arguments = browser_settings.get('arguments', {})
        options = browser_settings.get('options', {})

        # Apply arguments
        if arguments.get('no_sandbox'):
            chrome_options.add_argument('--no-sandbox')
        if arguments.get('dev_shm_usage'):
            chrome_options.add_argument('--disable-dev-shm-usage')
        if arguments.get('disable_gpu'):
            chrome_options.add_argument('--disable-gpu')
        if arguments.get('disable_automation'):
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

        # Apply options
        chrome_options.add_argument(f'--remote-debugging-port={options.get("debugging_port", "0")}')
        chrome_options.add_argument(f'--window-size={options.get("window_size", "1920,1080")}')
        chrome_options.add_argument(f'--user-agent={options.get("user_agent", "Mozilla/5.0")}')

        service = Service(ChromeDriverManager().install())

        print("Creating Chrome driver...")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome driver created successfully")

        return self.driver

    def get_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        return self.init_driver()

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

browser_manager = BrowserManager()
