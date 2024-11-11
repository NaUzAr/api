# app/schemas.py

from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional

# Skema untuk Registrasi User
class UserCreate(BaseModel):
    name: str = Field(..., example="John Doe")
    username: str = Field(..., example="johndoe123")
    email: EmailStr = Field(..., example="johndoe@example.com")
    password: str = Field(..., min_length=6, example="password123")
    role: int = Field(..., example=2)
    disease: Optional[str] = Field(None, example="jantung")
    date_of_birth: date = Field(..., example="1990-01-01")
    place_of_birth: str = Field(..., example="New York")

# Skema untuk Response User
class UserResponse(BaseModel):
    id: int
    name: str
    username: str
    email: EmailStr
    role: int
    disease: Optional[str] = None
    date_of_birth: date
    place_of_birth: str

    class Config:
        orm_mode = True

# Skema untuk Login
class UserLogin(BaseModel):
    username: str = Field(..., example="johndoe123")
    password: str = Field(..., example="password123")

# Skema untuk Token
class Token(BaseModel):
    access_token: str
    token_type: str

# Skema untuk Token Data
class TokenData(BaseModel):
    username: Optional[str] = None
