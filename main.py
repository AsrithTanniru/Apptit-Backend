# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import models
from db import engine, get_db
from sqlalchemy import or_
from sqlalchemy.orm import Session
from models import Jobs, Users, JobRequest, GoogleAuthRequest, Preferences, PreferenceRequest,UpdatePreferences,JobPreferences,SavedJobs,SaveJobRequest
import chromedriver_autoinstaller
from scraper.linkedin import fetch_linkedin
from scraper.glassdoor import fetch_glassdoor
from scraper.scraper import scrape_all
from scraper.internshala import fetch_internshala


chromedriver_autoinstaller.install()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
    expose_headers=["*"], 
    max_age=86400,  
)
models.Base.metadata.create_all(bind=engine)

# MARK:User Routes
@app.get("/")
def home():
    return {"message": "Job Scraper API"}

@app.post("/auth/google")
async def google_auth(user_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        email = user_data.email
        name = user_data.name

        user = db.query(Users).filter(Users.email == email).first()
        
        if not user:
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

@app.get('/users/{user_id}/preferences')
# async def get_user_preferences(user_id: int, db: Session = Depends(get_db)):
#     prefs = db.query(Preferences).filter(Preferences.user_id == user_id).all()
#     return prefs
async def get_preferences(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
        prefs = db.query(Preferences).filter(Preferences.user_id == user_id).all()
        result = []
        for pref in prefs:
            result.append({
                "id": pref.id,
                "user_id": pref.user_id,
                "title": pref.title.split(",") if "," in pref.title else [pref.title],
                "location": pref.location.split(",") if "," in pref.location else [pref.location]
            })
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error retrieving preferences: {str(e)}')


#MARK:Preference Routes


# @app.post('/add-preferences')
# async def preferences(pref_request: PreferenceRequest, db: Session = Depends(get_db)):
#     try:
#         user = db.query(Users).filter(Users.id == pref_request.user_id).first()
#         if not user:
#             raise HTTPException(status_code=404, detail=f"User with ID {pref_request.user_id} not found")
#         new_pref = Preferences(
#             user_id = pref_request.user_id,
#             title = pref_request.title,
#             location = pref_request.location,
#         )
#         db.add(new_pref)
#         db.commit()
#         db.refresh(new_pref)

#         return {f"Updated prefernces with {pref_request.title} and {pref_request.location}"}
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f'Error storing preferences:{str(e)}')

@app.post('/add-preferences')
async def save_preferences(pref_request: PreferenceRequest, db: Session = Depends(get_db)):
    try:

        user_id = pref_request.user_id
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        titles_str = ",".join(pref_request.title)
        locations_str = ",".join(pref_request.location)
        
        new_pref = Preferences(
            user_id=user_id,
            title=titles_str,
            location=locations_str
        )
        
        db.add(new_pref)
        db.commit()
        db.refresh(new_pref)
        
        return {f"Updated prefernces with {new_pref.title} and {new_pref.location}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f'Error storing preferences: {str(e)}')

@app.patch('/update-preferences')
async def update_preferences(update_pref: UpdatePreferences, db: Session = Depends(get_db)):
    try:
        user_id = update_pref.user_id
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        
        pref = db.query(Preferences).filter(Preferences.user_id == user_id).first()
        if not pref:
            raise HTTPException(status_code=404, detail=f"No preferences found for user {user_id}")
        
        if update_pref.title:
            pref.title = ",".join(update_pref.title)
        if update_pref.location:
            pref.location = ",".join(update_pref.location)

        db.commit()
        db.refresh(pref)

        return {"message": f"Updated preferences to titles: {pref.title} and locations: {pref.location}"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f'Error updating preferences: {str(e)}')
    

@app.get('/jobs-user-preferences/{user_id}')
async def get_jobs_by_pref(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")

        prefs = db.query(Preferences).filter(Preferences.user_id == user_id).first()
        if not prefs:
            raise HTTPException(status_code=404, detail="No preferences found for this user")

        titles = prefs.title.split(",")
        locations = prefs.location.split(",")

        # Debug print
        print("Searching jobs for:", titles, locations)

        jobs = db.query(Jobs).filter(
            or_(*[Jobs.title.ilike(f"%{t.strip()}%") for t in titles]),
            or_(*[Jobs.location.ilike(f"%{l.strip()}%") for l in locations])
        ).all()

        return {"Jobs Based on your preferences":  jobs,
                "Total Jobs": len(jobs)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed fetching jobs based on your preferences: {str(e)}")


#  MARK:Scraper Routes
@app.post("/scrape_jobs")
async def scrape_all_jobs(job_request: JobRequest, db: Session = Depends(get_db)):
    try:
        existing_jobs = db.query(Jobs).filter(
            Jobs.title.ilike(f"%{job_request.keyword}%"),
            Jobs.location.ilike(f"%{job_request.location}%")
        ).all()
        
        if len(existing_jobs) >= 20:  
            return {
                "message": "Existing jobs from database",
                "jobs": existing_jobs,
                "count": len(existing_jobs)
            }
        
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
        return {
            "message": " jobs scraped and added ",
            "jobs": db_jobs,
            "count": len(db_jobs)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing job request: {str(e)}")

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
    


#MARK:Filter Routes
@app.get("/jobs")
async def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Jobs).all()
    return jobs


@app.get('/search-jobs/{keyword}')
async def get_searched_jobs(keyword: str, db: Session= Depends(get_db)):
    try: 
        jobs = db.query(Jobs).filter(Jobs.title.ilike(f'{keyword}%')).all()

    except:
        raise HTTPException(status_code=404, detail=f'The requested {keyword} job search did not find any results!')
    return jobs

#MARK: Saved Jobs
@app.post('/save-job')
async def save_job(data: SaveJobRequest, db: Session = Depends(get_db)):
    existing = db.query(SavedJobs).filter(
        SavedJobs.user_id == data.user_id,
        SavedJobs.job_id == data.job_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Job already saved")

    saved = SavedJobs(user_id=data.user_id, job_id=data.job_id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return {"message": "Job saved successfully", "saved_job_id": saved.id}

@app.get('/saved-jobs/{user_id}')
async def get_saved_jobs(user_id: int, db: Session = Depends(get_db)):
    saved = db.query(SavedJobs).filter(SavedJobs.user_id == user_id).all()
    jobs = [s.job for s in saved]
    return {"Saved Jobs": jobs, "Total Saved Jobs": len(jobs)}

@app.delete('/unsave-job')
async def unsave_job(data: SaveJobRequest, db: Session = Depends(get_db)):
    saved = db.query(SavedJobs).filter(
        SavedJobs.user_id == data.user_id,
        SavedJobs.job_id == data.job_id
    ).first()

    if not saved:
        raise HTTPException(status_code=404, detail="Saved job not found")

    db.delete(saved)
    db.commit()
    return {"message": "Job unsaved successfully"}






