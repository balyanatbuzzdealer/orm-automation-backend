import os
import csv
import random
import base64
import requests
import json
import time
import uuid
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

owner = 'balyanatbuzzdealer'  # GitHub username or organization name
repo = os.getenv('GITHUB_REPO')  # Repository name
token = os.getenv('GITHUB_TOKEN') # Your GitHub token


# Specify the path to your ChromeDriver
chromedriver_path = "/Users/davidbalian/Downloads/chromedriver-mac-arm64/chromedriver"  # Update if needed

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

def upload_to_github(file_content, filename):
    """Uploads a file to GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
    encoded_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')
    message = f"Upload {filename} via scraper"

    # Check if the file exists to get the SHA for update, or create a new file
    response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
    sha = response.json().get('sha') if response.status_code == 200 else None

    body = {
        "message": message,
        "content": encoded_content,
        "branch": "main"
    }
    if sha:
        body["sha"] = sha

    headers = {'Authorization': f'Bearer {token}'}
    response = requests.put(url, headers=headers, data=json.dumps(body))

    if response.status_code in [200, 201]:
        print(f"File uploaded successfully: {filename}")
    else:
        print(f"Error uploading file: {filename} - {response.status_code}, {response.text}")

def generate_jsdelivr_url(filename):
    """Generates a jsDelivr URL for the file on GitHub."""
    return f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@main/{filename}"

def save_csv_to_github(search_term, search_results):
    """Saves search results to a CSV file, uploads it to GitHub, and returns the jsDelivr URL."""
    filename = f"{search_term}_{uuid.uuid4()}.csv"
    file_path_local = os.path.join("output", filename)  # Local temporary file
    
    os.makedirs(os.path.dirname(file_path_local), exist_ok=True)
    
    # Save search results to CSV locally
    with open(file_path_local, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Link"])
        for result in search_results:
            writer.writerow([result["title"], result["link"]])

    try:
        with open(file_path_local, 'r') as file:
            file_content = file.read()
        
        # Upload the CSV to GitHub
        upload_to_github(file_content, f"search_results/{filename}")
        os.remove(file_path_local)  # Delete local file after upload
        
        # Return jsDelivr URL
        return generate_jsdelivr_url(f"search_results/{filename}")

    except Exception as e:
        print(f"Error uploading to GitHub: {e}")
        return None

def capture_screenshot_github(driver, search_term):
    """Captures a screenshot, uploads it to GitHub, and returns the jsDelivr URL."""
    screenshot_filename = f"{search_term}_{uuid.uuid4()}.png"
    screenshot_path_local = os.path.join("output", screenshot_filename)

    try:
        driver.save_screenshot(screenshot_path_local)  # Save locally first
        
        with open(screenshot_path_local, 'rb') as file:
            screenshot_content = base64.b64encode(file.read()).decode('utf-8')
        
        # Upload the screenshot to GitHub
        upload_to_github(screenshot_content, f"screenshots/{screenshot_filename}")
        os.remove(screenshot_path_local)  # Delete local file after upload
        
        # Return jsDelivr URL
        return generate_jsdelivr_url(f"screenshots/{screenshot_filename}")

    except Exception as e:
        print(f"Error capturing or uploading screenshot: {e}")
        return None

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
            result_elements = driver.find_elements(By.XPATH, "//div[@class='tF2Cxc']")  # Example XPath, adjust as needed

            for result in result_elements[:num_results]:  # Limit to num_results
                try:
                    title = result.find_element(By.TAG_NAME, "h3").text
                    link = result.find_element(By.TAG_NAME, "a").get_attribute("href")
                    search_results.append({"title": title, "link": link})
                except Exception as e:
                    print(f"Skipping result due to error: {e}")

            # Save to CSV and get jsDelivr URL
            csv_url = save_csv_to_github(search_term, search_results)
            print(f"CSV for '{search_term}' saved to: {csv_url}")

            # Capture screenshot and get jsDelivr URL
            screenshot_url = capture_screenshot_github(driver, search_term)
            if screenshot_url:
                print(f"Screenshot for '{search_term}' saved to: {screenshot_url}")
            else:
                print(f"Screenshot capture failed for '{search_term}'")

            # Store the URLs for the current search term
            results[search_term] = {
                "csv": csv_url,
                "screenshot": screenshot_url
            }

        return {"status": "success", "files": results}

    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

    finally:
        driver.quit()
