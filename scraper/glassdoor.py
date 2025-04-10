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

chromedriver_autoinstaller.install() 
from bs4 import BeautifulSoup
import time


def fetch_glassdoor(keyword, location):
    try:
        try:
            import chromedriver_autoinstaller
            chromedriver_autoinstaller.install()
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--start-maximized")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
            try:
                driver = webdriver.Chrome(options=options)
            except Exception as e:
                print(f"Failed to initialize with autoinstaller: {e}")
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
            
            results = []
            base_url = "https://www.glassdoor.co.in"
            
            print(f"Accessing Glassdoor job search page...")
            driver.get(f"{base_url}/Job/jobs.htm")
            
            wait = WebDriverWait(driver, 10)
            time.sleep(3)
            
            try:
                print("Entering search criteria...")
                keyword_input = wait.until(EC.presence_of_element_located((By.ID, "searchBar-jobTitle")))
                keyword_input.clear()
                keyword_input.send_keys(keyword)
                
                location_input = wait.until(EC.presence_of_element_located((By.ID, "searchBar-location")))
                location_input.clear()
                location_input.send_keys(location)

                print("Submitting search...")
                location_input.send_keys(Keys.RETURN)
                time.sleep(5)
                
            except Exception as e:
                print(f"Search form error: {e}")
                # Fallback to URL construction
                driver.save_screenshot("search_error.png")
                loc_slug = location.lower().replace(' ', '-')
                keyword_slug = keyword.lower().replace(' ', '-')
                url = f"{base_url}/Job/{loc_slug}-{keyword_slug}-jobs-SRCH_IL.0,{len(loc_slug)}_IN115_KO{len(loc_slug)+1},{len(loc_slug)+1+len(keyword_slug)}.htm"
                print(f"Using direct URL: {url}")
                driver.get(url)
            
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-test='jobListing']")))
                print("Job listings loaded, attempting to load more...")
                
                for i in range(3):  
                    try:
                        loadmore_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='load-more']")))
                        driver.execute_script("arguments[0].scrollIntoView();", loadmore_button)
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", loadmore_button)
                        
                        try:
                            popup = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "CloseButton")))
                            popup.click()
                            time.sleep(1)  
                        except Exception:
                            pass
                            
                        print(f"Loaded more jobs (attempt {i+1}/3)")
                        time.sleep(3)  
                    except Exception as e:
                        print(f"Could not load more jobs: {e}")
                        break 
                
                html = driver.page_source
                soup = BeautifulSoup(html, "html.parser")
                
                jobs = soup.select("li.JobsList_jobListItem__wjTHv, li[data-test='jobListing']")
                tot_jobs = len(jobs)
                print(f"Total Glassdoor jobs found: {tot_jobs}")
        

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


                        if link:
                            if link.startswith("/partner/jobListing.htm"):
                                link = base_url + link
                            elif not link.startswith("http"):
                                link = base_url + link
                        else:
                            link = "N/A"
                        
                        job_data = {
                            "title": title,
                            "company": company,
                            "location": job_location,
                            "link": link,
                            "platform":"Glassdoor"
                        }
                        
                        results.append(job_data)
                    except Exception as e:
                        print(f"Error extracting job details: {e}")
                        continue
                
                return {"total_jobs": tot_jobs, "jobs": results}
                
            except Exception as e:
                print(f"Error processing job listings: {e}")
                driver.save_screenshot("job_list_error.png")
                return {"error": f"Job listing processing error: {e}"}
                
        except Exception as e:
            print(f"Error with ChromeDriver setup: {e}")
            return {"error": f"ChromeDriver setup failed: {e}"}
            
    except Exception as e:
        print(f"General error in Glassdoor scraper: {e}")
        return {"error": str(e)}
        
    finally:
        if 'driver' in locals():
            driver.quit()
