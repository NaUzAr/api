# app/models.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)
    disease = Column(String)
    date_of_birth = Column(String)
    place_of_birth = Column(String)

    data_entries = relationship("DataEntry", back_populates="owner")

class DataEntry(Base):
    __tablename__ = 'data_entries'

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    string_field1 = Column(String)
    string_field2 = Column(String)
    string_field3 = Column(String)
    int_field1 = Column(Integer)
    int_field2 = Column(Integer)
    int_field3 = Column(Integer)
    int_field4 = Column(Integer)
    int_field5 = Column(Integer)
    int_field6 = Column(Integer)
    int_field7 = Column(Integer)
    int_field8 = Column(Integer)

    owner = relationship("User", back_populates="data_entries")
