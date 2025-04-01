from pydantic import BaseModel, EmailStr, Field
class JobRequest(BaseModel):
    keyword: str
    location: str