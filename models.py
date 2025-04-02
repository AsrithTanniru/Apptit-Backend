# models.py
from pydantic import BaseModel
from db import Base
from sqlalchemy import Column, Integer, String

class JobRequest(BaseModel):
    keyword: str
    location: str

class GoogleAuthRequest(BaseModel):
    name: str
    email: str
    
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
