# app/schemas.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer

# Tambahkan OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Skema User
class UserBase(BaseModel):
    name: str
    username: str
    email: str
    role: str
    disease: str
    date_of_birth: str  # Jika ingin menggunakan Date, ubah tipe ini
    place_of_birth: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True

# Skema Login
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Skema DataEntry
class DataEntryBase(BaseModel):
    string_field1: str
    string_field2: str
    string_field3: str
    int_field1: int
    int_field2: int
    int_field3: int
    int_field4: int
    int_field5: int
    int_field6: int
    int_field7: int
    int_field8: int

class DataEntryCreate(DataEntryBase):
    pass

class DataEntryUpdate(DataEntryBase):
    pass

class DataEntryResponse(DataEntryBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

# Skema ActivityLog
class ActivityLogBase(BaseModel):
    action: str

class ActivityLogCreate(ActivityLogBase):
    pass

class ActivityLogResponse(ActivityLogBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        orm_mode = True
