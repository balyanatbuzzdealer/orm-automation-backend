import os
import csv
import random
import time
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import firebase_admin
from firebase_admin import credentials, storage

cred = credentials.Certificate({
  "type": "service_account",
  "project_id": "orm-automation-app",
  "private_key_id": "c5ee1c103cf46319b7b01ed1e75db2a73ca38402",
  "private_key": os.environ.get("FIRESTORE"),  # Corrected: get private key from env variable
  "client_email": "firebase-adminsdk-fbsvc@orm-automation-app.iam.gserviceaccount.com",
  "client_id": "117641343782622588074",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40orm-automation-app.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
})

firebase_admin.initialize_app(cred, {
    'storageBucket': 'orm-automation-app.appspot.com'  # Replace with your Firebase storage bucket name
})


# List of random user-agents to avoid detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]

# Firebase Storage bucket
bucket = storage.bucket()

# Function to initialize and configure the browser
def setup_browser(country):
    """Initializes the Chrome driver and opens Google."""
    user_agent = random.choice(USER_AGENTS)
    
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
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
        time.sleep(random.uniform(3, 5))
    except Exception:
        print("No cookie popup found or already accepted.")

    return driver

# Function to save results to CSV
def save_to_csv(search_term, search_results):
    """Saves search results to a CSV file."""
    filename = f"{search_term}_{uuid.uuid4()}.csv"
    file_path = os.path.join("output", filename)
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Link"])
        for result in search_results:
            writer.writerow([result["title"], result["link"]])
    
    return file_path

# Function to capture a screenshot
def capture_screenshot(driver, search_term):
    """Captures a screenshot for a given search term."""
    screenshot_filename = f"{search_term}_{uuid.uuid4()}.png"
    screenshot_path = os.path.join("output", screenshot_filename)
    
    driver.save_screenshot(screenshot_path)
    
    return screenshot_path

# Function to upload a file to Firebase Storage
def upload_to_firebase(file_path):
    """Uploads a file to Firebase Storage and returns its public URL."""
    blob = bucket.blob(os.path.basename(file_path))
    blob.upload_from_filename(file_path)
    blob.make_public()
    return blob.public_url

# Function to scrape search results, save to CSV, capture screenshots, and upload to Firebase
def scrape_google_search(search_terms_string, country, num_results):
    """Searches multiple terms in one browser session, saves results, captures screenshots, and uploads to Firebase."""
    search_terms = [term.strip() for term in search_terms_string.split(",") if term.strip()]
    driver = setup_browser(country)
    
    results = {}

    try:
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

            # Extract search results (title & link)
            search_results = []
            result_elements = driver.find_elements(By.XPATH, "//div[@class='tF2Cxc']")
            
            for result in result_elements[:num_results]:  # Limit to num_results
                try:
                    title = result.find_element(By.TAG_NAME, "h3").text
                    link = result.find_element(By.TAG_NAME, "a").get_attribute("href")
                    search_results.append({"title": title, "link": link})
                except Exception as e:
                    print(f"Skipping result due to error: {e}")
            
            # Save results to CSV and capture screenshot
            csv_file_path = save_to_csv(search_term, search_results)
            screenshot_file_path = capture_screenshot(driver, search_term)
            
            # Upload files to Firebase Storage
            csv_url = upload_to_firebase(csv_file_path)
            screenshot_url = upload_to_firebase(screenshot_file_path)

            # Add file URLs to results
            results[search_term] = {
                "csv": csv_url,
                "screenshot": screenshot_url
            }

        return {"status": "success", "results": results}

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

    finally:
        driver.quit()
