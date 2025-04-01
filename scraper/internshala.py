from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup

def fetch_internshala(keyword, location=None, max_pages=3):
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    results = []
    
    try:
        base_url = "https://internshala.com/internships"
        url = f"{base_url}/keywords-{keyword.replace(' ', '-')}"

        if location:
            url += f"/location-{location.replace(' ', '-')}"
        
        print(f"Fetching internships from: {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "individual_internship")))

        page = 1
        while page <= max_pages:
            print(f"Scraping page {page}...")

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            internships = soup.find_all("div", class_="individual_internship")
            print(f"Found {len(internships)} internships on page {page}")

            if not internships:
                break 

            for internship in internships:
                try:
                    title_elem = internship.find("a", class_="job-title-href")
                    title = title_elem.text.strip() if title_elem else "N/A"
                    link = f"https://internshala.com{title_elem['href']}" if title_elem and title_elem.get("href") else "N/A"
                    
                    company_elem = internship.find("p", class_="company-name")
                    company = company_elem.text.strip() if company_elem else "N/A"

                    location_elem = internship.find("div", class_="locations")
                    location = location_elem.text.strip() if location_elem else "N/A"

                    # duration_elem = internship.find("i", class_="ic-16-calendar")
                    # duration = duration_elem.find_next_sibling("span").text.strip() if duration_elem else "N/A"

                    # stipend_elem = internship.find("span", class_="stipend")
                    # stipend = stipend_elem.text.strip() if stipend_elem else "N/A"

                    # posted_elem = internship.find("div", class_="status-inactive")
                    # posted = posted_elem.find("span").text.strip() if posted_elem else "N/A"

                    # actively_hiring = bool(internship.find("div", class_="actively-hiring-badge"))

                    results.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        # "duration": duration,
                        # "stipend": stipend,
                        # "posted": posted,
                        # "actively_hiring": actively_hiring,
                        "link": link,
                        "platform":"Internshala"
                    })
                
                except Exception as e:
                    print(f"Error parsing internship: {e}")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3) 
            try:
                next_button = driver.find_element(By.XPATH, "//a[contains(text(),'Next')]")
                
                if "disabled" in next_button.get_attribute("class"):
                    print("Next button is disabled. Ending scraping.")
                    break
                
                print(f"navigating to page {page + 1}...")
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(5)  

                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "individual_internship")))

                page += 1

            except Exception:
                print("No button found,scrolling.")
                break 

    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        driver.quit()
    
    results.pop(0)
    return results
