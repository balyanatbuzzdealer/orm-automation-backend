import os
import csv
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_browser(country):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=2560,1920")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chromedriver_path = "./chromedriver-mac-arm64/chromedriver"

    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(f"https://{country}")
    
    time.sleep(random.uniform(2, 4))
    
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Accept all')]"))
        )
        accept_button = driver.find_element(By.XPATH, "//div[contains(text(), 'Accept all')]/ancestor::button")
        accept_button.click()
        time.sleep(random.uniform(3, 5))
    except Exception:
        pass
    
    return driver

def scrape_google_search(search_terms_string, country, num_results):
    search_terms = [term.strip() for term in search_terms_string.split(",") if term.strip()]
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    driver = setup_browser(country)
    
    all_results = []
    
    try:
        for search_term in search_terms:
            print(f"Searching for: {search_term}")
            search_url = f"https://www.google.com/search?q={search_term}&num={num_results}"
            driver.get(search_url)
            time.sleep(random.uniform(3, 6))
            
            screenshot_filename = f"{search_term.replace(' ', '_')}_screenshot.png"
            screenshot_path = os.path.join(output_dir, screenshot_filename)
            driver.save_screenshot(screenshot_path)

            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            time.sleep(5)

            search_results = []
            result_elements = driver.find_elements(By.XPATH, "//a[.//h3[normalize-space()]]") #Modified XPATH

            for result in result_elements[:num_results]:
                try:
                    title = result.find_element(By.XPATH, ".//h3").text
                    link = result.get_attribute("href")
                    search_results.append({"title": title, "link": link})
                except Exception as e:
                    print(f"Error extracting result: {e}")

            csv_filename = f"{search_term.replace(' ', '_')}_results.csv"
            csv_path = os.path.join(output_dir, csv_filename)
            with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Title", "Link"])
                for result in search_results:
                    writer.writerow([result["title"], result["link"]])

            all_results.append({
                "search_term": search_term,
                "csv_file": "https://localhost:8000/" + csv_path,
                "screenshot_file": "https://localhost:8000/" +  screenshot_path
            })
        
        return {"results": all_results}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    finally:
        driver.quit()