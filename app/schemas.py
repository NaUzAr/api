# app/schemas.py

from pydantic import BaseModel, EmailStr, constr
from datetime import date
from typing import List

# Skema untuk membuat pengguna baru
class UserCreate(BaseModel):
    name: str
    username: str
    email: EmailStr
    password: constr(min_length=6)  # Password minimal 6 karakter
    role: int
    disease: str
    date_of_birth: date
    place_of_birth: str

# Skema untuk respon pengguna
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

# Skema untuk autentikasi token
class Token(BaseModel):
    access_token: str
    token_type: str

# Skema untuk permintaan login menggunakan JSON
class LoginRequest(BaseModel):
    username: str
    password: str

# Skema untuk membuat postingan baru dengan token di body
class PostCreateWithToken(BaseModel):
    access_token: str
    title: str
    content: str
    published: bool = True

# Skema untuk respon postingan
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    published: bool
    owner_id: int

    class Config:
        orm_mode = True
