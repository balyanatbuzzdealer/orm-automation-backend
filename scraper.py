import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# List of random user-agents to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]

# Function to initialize and configure the browser
def setup_browser(country):
    """Initializes the Chrome driver and opens Google."""
    user_agent = random.choice(USER_AGENTS)
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)
    driver.get(f"https://{country}")
    
    time.sleep(random.uniform(2, 4))

    # Accept Cookies if present
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Accept all')]"))
        )
        accept_button = driver.find_element(By.XPATH, "//div[contains(text(), 'Accept all')]/ancestor::button")
        accept_button.click()
        print("Cookie popup accepted.")
        time.sleep(random.uniform(3, 5))
    except Exception:
        print("No cookie popup found or already accepted.")

    return driver

# Function to scrape search results and log to console
def scrape_google_search(search_terms_string, country, num_results):
    """Searches multiple terms in one browser session, logs results to console."""
    search_terms = [term.strip() for term in search_terms_string.split(",") if term.strip()]
    driver = setup_browser(country)

    try:
        print(f"Browser opened for country: {country}")
        print(f"Searching for: {search_terms_string}")
        
        for search_term in search_terms:
            print(f"Searching for: {search_term}")

            # Locate search box before each search
            search_box = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Clear previous search
            search_box.clear()
            time.sleep(random.uniform(0.5, 1.5))

            # Type search term and submit
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(3, 6))

            # Log screenshot equivalent (just logging here for now)
            print(f"Would save screenshot for: {search_term}")

            # Extract search results (title & link)
            search_results = []
            results = driver.find_elements(By.XPATH, "//div[@class='tF2Cxc']")
            
            for result in results[:num_results]:  # Limit to num_results
                try:
                    title = result.find_element(By.TAG_NAME, "h3").text
                    link = result.find_element(By.TAG_NAME, "a").get_attribute("href")
                    search_results.append([title, link])
                    print(f"Found result: {title} - {link}")
                except Exception as e:
                    print(f"Skipping result due to error: {e}")

        return {"status": "success", "message": "All searches completed."}

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

    finally:
        driver.quit()
