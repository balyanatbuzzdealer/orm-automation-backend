import csv
import os
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
    
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)
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

# Function to scrape search results and save them to CSV
def scrape_google_search(search_terms_string, country, num_results):
    """Searches multiple terms in one browser session, takes screenshots, and saves results."""
    search_terms = [term.strip() for term in search_terms_string.split(",") if term.strip()]
    driver = setup_browser(country)

    try:
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        if not os.path.exists("csv_results"):
            os.makedirs("csv_results")

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

            # Save screenshot
            screenshot_path = f"screenshots/{search_term.replace(' ', '_')}.png"
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved at: {screenshot_path}")

            # Extract search results (title & link)
            search_results = []
            results = driver.find_elements(By.XPATH, "//div[@class='tF2Cxc']")
            
            for result in results[:num_results]:  # Limit to num_results
                try:
                    title = result.find_element(By.TAG_NAME, "h3").text
                    link = result.find_element(By.TAG_NAME, "a").get_attribute("href")
                    search_results.append([title, link])
                except Exception as e:
                    print(f"Skipping result due to error: {e}")

            # Save results to CSV
            csv_filename = f"csv_results/{search_term.replace(' ', '_')}.csv"
            with open(csv_filename, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Title", "Link"])
                writer.writerows(search_results)

            print(f"Results saved in: {csv_filename}")

        return {"status": "success", "message": "All searches completed."}

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

    finally:
        driver.quit()
