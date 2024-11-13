# app/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Pastikan ini String
    disease = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)  # Atau ubah ke Date
    place_of_birth = Column(String, nullable=True)

    data_entries = relationship("DataEntry", back_populates="owner")
    activity_logs = relationship("ActivityLog", back_populates="user")

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

class ActivityLog(Base):
    __tablename__ = 'activity_logs'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activity_logs")
