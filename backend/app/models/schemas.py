from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str = Field(alias="_id")
    plan: str = "FREE"
    created_at: datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProjectBase(BaseModel):
    title: str

class Project(ProjectBase):
    id: str = Field(alias="_id")
    user_id: str
    status: str = "DRAFT"
    created_at: datetime
    updated_at: datetime
