# models.py
from datetime import datetime
from pydantic import BaseModel
from db import Base
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, ARRAY
from sqlalchemy.orm import relationship
from typing import List,Optional

class JobRequest(BaseModel):
    keyword: str
    location: str

class GoogleAuthRequest(BaseModel):
    name: str
    email: str

class PreferenceRequest(BaseModel):
    user_id: int
    title: List[str]
    location: List[str]

class GetPreferences(BaseModel):
    user_id: int
    
class UpdatePreferences(BaseModel):
    user_id: int
    title: Optional[List[str]] = None
    location: Optional[List[str]] = None

class JobPreferences(BaseModel):
    title:List[str]
    location:List[str]

class SaveJobRequest(BaseModel):
    user_id: int
    job_id: int


class Jobs(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, nullable=False)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=False)
    link = Column(String, nullable=False)
    platform = Column(String, nullable=False)

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    picture = Column(String, nullable=True)
    preferences = relationship("Preferences", back_populates="user")
    saved_jobs = relationship("SavedJobs", back_populates="user")



class Preferences(Base):
    __tablename__ = 'preferences'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String, nullable=False)
    location = Column(String, nullable=False)
    user = relationship("Users", back_populates="preferences")

class SavedJobs(Base):
    __tablename__ = 'savedjobs'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    job_id = Column(Integer, ForeignKey('jobs.id'))
    saved_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Users", back_populates="saved_jobs")
    job = relationship("Jobs")
