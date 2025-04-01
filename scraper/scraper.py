from scraper.linkedin import fetch_linkedin
from scraper.glassdoor import fetch_glassdoor
from scraper.internshala import fetch_internshala
from models import JobRequest
import concurrent.futures
from functools import partial
from models import JobRequest

def scrape_all(job: JobRequest):
    print("Scrape_all called...")
    print("Scraping all jobs...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        linkedin_future = executor.submit(fetch_linkedin, job.keyword, job.location)
        glassdoor_future = executor.submit(fetch_glassdoor, job.keyword, job.location)
        internshala_future = executor.submit(fetch_internshala, job.keyword, job.location)
        
        linkedin_results = linkedin_future.result()
        glassdoor_results = glassdoor_future.result()
        internshala_results = internshala_future.result()

    linkedin_jobs = []
    if isinstance(linkedin_results, list):
        linkedin_jobs = linkedin_results
    elif isinstance(linkedin_results, dict):
        if "error" not in linkedin_results:
            linkedin_jobs = linkedin_results.get("jobs", [])

    glassdoor_jobs = []
    if isinstance(glassdoor_results, dict):
        if "error" not in glassdoor_results:
            glassdoor_jobs = glassdoor_results.get("jobs", [])
    elif isinstance(glassdoor_results, list):
        glassdoor_jobs = glassdoor_results

    internshala_jobs = []
    if isinstance(internshala_results,list):
        internshala_jobs = internshala_results
    elif isinstance(internshala_results, dict):
        if "error" not in internshala_results:
            internshala_jobs = internshala_results.get("jobs", [])

    
    all_jobs = linkedin_jobs + glassdoor_jobs+internshala_jobs
    return all_jobs


# def scrape_all(keyword, location):
#     linkedin_jobs = fetch_linkedin(keyword, location)
#     glassdoor_jobs = fetch_glassdoor(keyword, location)
#     return linkedin_jobs + glassdoor_jobs