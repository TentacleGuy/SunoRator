from utils.thread_manager import thread_manager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def start_scraping(stop_event, log_queue):
    try:
        chrome_options = Options()
        if settings_manager.settings['scraper']['headless']:
            chrome_options.add_argument('--headless')
            
        driver = webdriver.Chrome(options=chrome_options)
        
        while not stop_event.is_set():
            # Scraping logic here
            log_queue.put("Scraping in progress...")
            
    except Exception as e:
        log_queue.put(f"Error: {str(e)}")
    finally:
        driver.quit()

def handle_scrape_request():
    return thread_manager.start_thread('scraper', start_scraping)
