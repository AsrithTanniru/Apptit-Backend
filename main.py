from fastapi import FastAPI
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller
import concurrent.futures
from functools import partial

chromedriver_autoinstaller.install() 
from bs4 import BeautifulSoup
import time
from fastapi.middleware.cors import CORSMiddleware


# Fastapi
app = FastAPI()
EMAIL = 'favidap835@dmener.com'
PASSWORD = "Test@123"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class JobRequest(BaseModel):
    keyword: str
    location: str

def fetch_linkedin(keyword, location):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        results = []
        url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
        driver.get(url)
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "base-card")))
        try:
            dismiss_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.modal__dismiss")))
            dismiss_button.click()
            time.sleep(1)
        except Exception as e:
            print(e)

        for _ in range(10):
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(1)
            try:
                dismiss_button = driver.find_element(By.CSS_SELECTOR, "button.modal__dismiss")
                dismiss_button.click()
            except:
                pass
            
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        jobs = soup.find_all("div", class_="base-card")
        print(f"\nTotal jobs: {len(jobs)}\n")
        
        for job in jobs[:200]:
            title = job.find("h3", class_="base-search-card__title")
            company = job.find("h4", class_="base-search-card__subtitle")
            job_location = job.find("span", class_="job-search-card__location")
            link = job.find("a", class_="base-card__full-link")
            
            job_data = {
                "title": title.text.strip() if title else "N/A",
                "company": company.text.strip() if company else "N/A",
                "location": job_location.text.strip() if job_location else "N/A",
                "link": link["href"] if link and link.has_attr("href") else "N/A"
            }
            results.append(job_data)
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        driver.quit()
        
    return results


def fetch_glassdoor(keyword, location):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")

    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 5)
    
    try:
        results = []
        base_url = "https://www.glassdoor.co.in"
        driver.get(f"{base_url}/Job/jobs.htm")
        time.sleep(3)
        try:
            keyword_input = wait.until(EC.presence_of_element_located((By.ID, "searchBar-jobTitle")))
            keyword_input.clear()
            keyword_input.send_keys(keyword)
            
            location_input = wait.until(EC.presence_of_element_located((By.ID, "searchBar-location")))
            location_input.clear()
            location_input.send_keys(location)

            location_input.send_keys(Keys.RETURN)
            time.sleep(5)
            
            # resulting 
            current_url = driver.current_url
            
        except Exception as e:
            driver.save_screenshot("search_error.png")
            loc_slug = location.lower().replace(' ', '-')
            keyword_slug = keyword.lower().replace(' ', '-')
            url = f"{base_url}/Job/{loc_slug}-{keyword_slug}-jobs-SRCH_IL.0,{len(loc_slug)}_IN115_KO{len(loc_slug)+1},{len(loc_slug)+1+len(keyword_slug)}.htm"
            driver.get(url)
        
        # jobs
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-test='jobListing']")))
            # //show more
            for _ in range(3):  
                try:
                    
                    loadmore_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='load-more']")))
                    driver.execute_script("arguments[0].scrollIntoView();", loadmore_button)
                    time.sleep(1) 
                    loadmore_button.click()
                    try:
                        popup = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "CloseButton")))
                        popup.click()
                        time.sleep(2)  
                    except Exception:
                        print("No login popup")
                    print("Show more jobs")
                    time.sleep(3)  
                except Exception as e:
                    print(f"Could not click: {str(e)}")
                    break 
            
            # bs4
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
           
            jobs = soup.select("li.JobsList_jobListItem__wjTHv, li[data-test='jobListing']")
            tot_jobs = len(jobs)
            print(f"\nTotal Glassdoor jobs found: {tot_jobs}\n")
    
            #  job details from class's names
            for job in jobs[:200]:
                try:
                    title_element = job.select_one("a.JobCard_jobTitle__GLyJ1, a[data-test='job-title']")
                    title = title_element.text.strip() if title_element else "N/A"
                    
                    company_element = job.select_one("div.EmployerProfile_profileContainer__63w3R, div[id^='job-employer-']")
                    company = company_element.text.strip() if company_element else "N/A"
                    
                    location_element = job.select_one("div.JobCard_location__Ds1fM, div[data-test='emp-location']")
                    job_location = location_element.text.strip() if location_element else "N/A"
                    
                    link = None
                    if title_element and title_element.has_attr('href'):
                        link = title_element['href']
                    else:
                        tracking_link = job.select_one("a.JobCard_trackingLink__HMyun, a[data-test='job-link']")
                        if tracking_link and tracking_link.has_attr('href'):
                            link = tracking_link['href']

                    # Format the link - handle partner links correctly
                    if link:
                        if link.startswith("/partner/jobListing.htm"):
                            link = base_url + link
                        elif not link.startswith("http"):
                            link = base_url + link
                    else:
                        link = "N/A"
                    
                    #dictionary for object
                    job_data = {
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "link": link,
                    }
                    
                    results.append(job_data)
                except Exception as e:
                    print(f"Error extracting job details: {str(e)}")
                    continue
            
        except Exception as e:
            print(f"Error processing job listings: {str(e)}")
            driver.save_screenshot("job_list_error.png")
            
    except Exception as e:
        print(f"General error: {str(e)}")
        return {"error": str(e)}
        
    finally:
        driver.quit()
    
    return {"total_jobs": tot_jobs, "jobs": results}

# Routes
@app.get("/")
def home():
    return {"Job Scraper"}

@app.post("/linkedin_jobs")
async def scrape_linkedin(job: JobRequest):
    return fetch_linkedin(job.keyword, job.location)

@app.post("/glassdoor_jobs")
async def scrape_glassdoor(job: JobRequest):
    return fetch_glassdoor(job.keyword, job.location)

@app.post("/scrape_jobs")
async def scrape_all_jobs(job: JobRequest):
    #MultiThreading
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        linkedin= executor.submit(fetch_linkedin, job.keyword, job.location)
        glassdoor = executor.submit(fetch_glassdoor, job.keyword, job.location)
    
        linkedin_results = linkedin.result()
        glassdoor_results = glassdoor.result()
    
    return {
        "linkedin": linkedin_results,
        "glassdoor": glassdoor_results
    }