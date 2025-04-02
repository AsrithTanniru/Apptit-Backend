# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import models
from db import engine, get_db
from sqlalchemy.orm import Session
from models import Jobs, Users, JobRequest, GoogleAuthRequest
import chromedriver_autoinstaller
from scraper.linkedin import fetch_linkedin
from scraper.glassdoor import fetch_glassdoor
from scraper.scraper import scrape_all
from scraper.internshala import fetch_internshala


chromedriver_autoinstaller.install()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000", "*"],  # "*" allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
    expose_headers=["*"], 
    max_age=86400,  
)
models.Base.metadata.create_all(bind=engine)

# Routes
@app.get("/")
def home():
    return {"message": "Job Scraper API"}

@app.post("/auth/google")
async def google_auth(user_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        email = user_data.email
        name = user_data.name

        # Check if user exists
        user = db.query(Users).filter(Users.email == email).first()
        
        if not user:
            # Create new user
            new_user = Users(name=name, email=email)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return {"message": "New user created", "email": email, "user_id": new_user.id}
        
        return {"message": "User authenticated", "email": email, "user_id": user.id}
    except Exception as e:
        print(f"Error in google_auth: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get('/users')
async def get_users(db: Session = Depends(get_db)):
    users = db.query(Users).all()
    return users

@app.post("/scrape_jobs")
async def scrape_all_jobs(job_request: JobRequest, db: Session = Depends(get_db)):
    try:

        jobs = scrape_all(job_request)
        
        db_jobs = []
        for job in jobs:
            new_job = Jobs(
                title=job['title'],
                company=job['company'],
                location=job['location'],
                link=job['link'],
                platform=job['platform']
            )
            db.add(new_job)
            db_jobs.append(job)
        
        db.commit()
        return db_jobs
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error scraping jobs: {str(e)}")

@app.post("/linkedin_jobs")
async def scrape_linkedin_jobs(job_request: JobRequest, db: Session = Depends(get_db)):
    try:
        jobs = fetch_linkedin(job_request.keyword, job_request.location)
        
        for job in jobs:
            new_job = Jobs(
                title=job['title'],
                company=job['company'],
                location=job['location'],
                link=job['link'],
                platform=job['platform']
            )
            db.add(new_job)
        
        db.commit()
        return jobs
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error scraping LinkedIn jobs: {str(e)}")

@app.post("/glassdoor_jobs")
async def scrape_glassdoor_jobs(job_request: JobRequest, db: Session = Depends(get_db)):
    try:
        jobs = fetch_glassdoor(job_request.keyword, job_request.location)
        
        for job in jobs:
            new_job = Jobs(
                title=job['title'],
                company=job['company'],
                location=job['location'],
                link=job['link'],
                platform=job['platform']
            )
            db.add(new_job)
        
        db.commit()
        return jobs
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error scraping Glassdoor jobs: {str(e)}")

@app.post("/internshala_jobs")
async def scrape_internshala_jobs(job_request: JobRequest, db: Session = Depends(get_db)):
    try:
        jobs = fetch_internshala(job_request.keyword, job_request.location)
        
        for job in jobs:
            new_job = Jobs(
                title=job['title'],
                company=job['company'],
                location=job['location'],
                link=job['link'],
                platform=job['platform']
            )
            db.add(new_job)
        
        db.commit()
        return jobs
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error scraping Internshala jobs: {str(e)}")

@app.get("/jobs")
async def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Jobs).all()
    return jobs
@app.get('/users')
async def get_users(db: Session = Depends(get_db)):
    j = db.query(Users).all()
    return j 
