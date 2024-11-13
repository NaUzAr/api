# app/schemas.py

from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    name: str
    username: str
    email: str
    role: str
    disease: str
    date_of_birth: str
    place_of_birth: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

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
