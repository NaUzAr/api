# app/schemas.py

from pydantic import BaseModel, EmailStr
from datetime import date

class UserCreate(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: str
    role: int
    disease: str
    date_of_birth: date
    place_of_birth: str

class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: EmailStr
    role: int
    disease: str
    date_of_birth: date
    place_of_birth: str

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
