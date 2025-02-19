import os
import csv
import random
import time
import uuid
from supabase import create_client, Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chromedriver_path = "/Users/davidbalian/Downloads/chromedriver-mac-arm64/chromedriver"  # Update if needed

url: str = "https://zqjmxfuneoaaqppnjzfd.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpxam14ZnVuZW9hYXFwcG5qemZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk5NTcxMTcsImV4cCI6MjA1NTUzMzExN30.PFNYW-pwvMYB0JsR7h-HyV06Acadm1lSKvL7PMIuHLg"

try:
    supabase: Client = create_client(url, key)
    print("Successfully connected to Supabase!")

    # Optionally, you can make a simple test request to further confirm:
    try:
        response = supabase.auth.get_user()  # Or any other simple Supabase call
        if response.error:
            print(f"Supabase test request failed: {response.error}")
        else:
            print("Supabase test request successful.")
    except Exception as e:
        print(f"Error during Supabase test request: {e}")

except Exception as e:
    print(f"Failed to connect to Supabase: {e}")

csv_bucket_name = "CSVs"
screenshot_bucket_name = "Screenshots"

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
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(f"https://{country}")
    
    time.sleep(random.uniform(2, 4))

    # Accept Cookies if present
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Accept all')]"))
        )
        accept_button = driver.find_element(By.XPATH, "//div[contains(text(), 'Accept all')]/ancestor::button")
        accept_button.click()
        time.sleep(random.uniform(3, 5))
    except Exception:
        print("No cookie popup found or already accepted.")

    return driver

# Function to save results to CSV in Supabase Storage
def save_to_csv_supabase(search_term, search_results):
    """Saves search results to a CSV file in Supabase Storage."""
    filename = f"{search_term}_{uuid.uuid4()}.csv"
    file_path_local = os.path.join("output", filename) # Local temporary file
    
    os.makedirs(os.path.dirname(file_path_local), exist_ok=True)
    
    with open(file_path_local, mode='w', newline='', encoding='utf-8') as file:  # Save locally first
        writer = csv.writer(file)
        writer.writerow(["Title", "Link"])
        for result in search_results:
            writer.writerow([result["title"], result["link"]])
    
    try:
        with open(file_path_local, 'rb') as file:  # Open in binary mode for Supabase upload
            supabase.storage().from_(csv_bucket_name).upload(file=file, path=filename, file_options={})
        print(f"Results for '{search_term}' uploaded to Supabase Storage: {filename}")
        os.remove(file_path_local) # Delete local file after upload
        return filename # Return the filename for potential later use (e.g., linking in database)
    except Exception as e:
        print(f"Error uploading to Supabase Storage: {e}")
        return None

# Function to capture and save screenshot to Supabase Storage
def capture_screenshot_supabase(driver, search_term):
    """Captures a screenshot and saves it to Supabase Storage."""
    screenshot_filename = f"{search_term}_{uuid.uuid4()}.png"
    screenshot_path_local = os.path.join("output", screenshot_filename)

    try:
        driver.save_screenshot(screenshot_path_local) # Save locally first
        with open(screenshot_path_local, 'rb') as file:  # Open in binary mode for Supabase upload
            supabase.storage().from_(screenshot_bucket_name).upload(file=file, path=screenshot_filename, file_options={"content-type": "image/png"})
        print(f"Screenshot for '{search_term}' uploaded to Supabase Storage: {screenshot_filename}")
        os.remove(screenshot_path_local) # Delete local file after upload
        return screenshot_filename
    except Exception as e:
        print(f"Error capturing or uploading screenshot: {e}")
        return None


# Function to scrape and save to CSV
def scrape_google_search(search_terms_string, country, num_results):
    search_terms = [term.strip() for term in search_terms_string.split(",") if term.strip()]
    driver = setup_browser(country)
    results = {}

    try:
        for search_term in search_terms:
            print(f"Searching for: {search_term}")
            search_box = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            time.sleep(random.uniform(0.5, 1.5))
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(3, 6))

            search_results = []
            result_elements = driver.find_elements(By.XPATH, "//div[@class='tF2Cxc']") # Example XPath, adjust as needed

            for result in result_elements[:num_results]:  # Limit to num_results
                try:
                    title = result.find_element(By.TAG_NAME, "h3").text
                    link = result.find_element(By.TAG_NAME, "a").get_attribute("href")
                    search_results.append({"title": title, "link": link})
                except Exception as e:
                    print(f"Skipping result due to error: {e}")

            # Save to CSV
            csv_path = save_to_csv_supabase(search_term, search_results)
            print(f"Results for '{search_term}' saved to: {csv_path}")

            # Capture screenshot
            screenshot_path = capture_screenshot_supabase(driver, search_term)  # Call the function
            if screenshot_path:
                print(f"Screenshot for '{search_term}' saved to: {screenshot_path}")
            else:
                print(f"Screenshot capture failed for '{search_term}'")


            results[search_term] = search_results

        return {"status": "success", "results": results}

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

    finally:
        driver.quit()