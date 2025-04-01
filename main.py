from fastapi import FastAPI
from pydantic import BaseModel
from webdriver_manager.chrome import ChromeDriverManager
import chromedriver_autoinstaller
from scraper.linkedin import fetch_linkedin
from scraper.glassdoor import fetch_glassdoor
from scraper.scraper import scrape_all
from scraper.internshala import fetch_internshala
import concurrent.futures
from functools import partial
from models import JobRequest
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)


# Routes
@app.get("/")
def home():
    return {"Job Scraper Api"}

@app.post("/linkedin_jobs")
async def scrape_linkedin(job: JobRequest):
    return fetch_linkedin(job.keyword, job.location)

@app.post("/glassdoor_jobs")
async def scrape_glassdoor(job: JobRequest):
    return fetch_glassdoor(job.keyword, job.location)


@app.post("/internshala_jobs")
async def scrape_internshala(job: JobRequest):
    return fetch_internshala(job.keyword, job.location)

@app.post("/scrape_jobs")
async def scrape_all_jobs(job: JobRequest):
    return scrape_all(job)
    