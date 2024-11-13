# app/main.py

from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from . import models, schemas, auth
from .database import engine
from sqlalchemy.orm import Session
from .dependencies import get_db
from .logging_service import log_activity
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

# Membuat semua tabel (gunakan Alembic di produksi)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Management API dengan Static Bearer Token dan JWT")

# Endpoint untuk registrasi pengguna baru
@app.post("/register", response_model=schemas.ResponseModel)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Cek apakah username atau email sudah ada
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if existing_user:
        return schemas.ResponseModel(success=False, error="Username atau email sudah digunakan")
    
    hashed_password = auth.pwd_context.hash(user.password)
    db_user = models.User(
        name=user.name,
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        disease=user.disease,
        date_of_birth=user.date_of_birth,
        place_of_birth=user.place_of_birth
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError as e:
        db.rollback()
        return schemas.ResponseModel(success=False, error="Username atau email sudah digunakan")
    
    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"User {db_user.username} telah mendaftar."
    )
    log_activity(db, activity_log, db_user.id)

    return schemas.ResponseModel(success=True, data=schemas.UserResponse.from_orm(db_user))

# Endpoint untuk login - Mengembalikan JWT token dan profil pengguna
@app.post("/login", response_model=schemas.TokenResponse)
def login_for_access_token(form_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        return schemas.ResponseModel(success=False, error="Tidak valid username atau password")
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"User {user.username} telah melakukan login."
    )
    log_activity(db, activity_log, user.id)

    # Menyusun data respons
    response_data = {
        "access_token": access_token,
        "token_type": "bearer",
        "user_profile": schemas.UserResponse.from_orm(user)
    }

    return schemas.TokenResponse(success=True, data=response_data)

# Endpoint yang dilindungi menggunakan JWT
@app.get("/users/me/", response_model=schemas.ResponseModel)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    user_data = schemas.UserResponse.from_orm(current_user)
    return schemas.ResponseModel(success=True, data=user_data)

# Endpoint untuk membuat data entry baru
@app.post("/data_entries/", response_model=schemas.ResponseModel)
def create_data_entry(
    data_entry: schemas.DataEntryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    new_data_entry = models.DataEntry(
        string_field1=data_entry.string_field1,
        string_field2=data_entry.string_field2,
        string_field3=data_entry.string_field3,
        int_field1=data_entry.int_field1,
        int_field2=data_entry.int_field2,
        int_field3=data_entry.int_field3,
        int_field4=data_entry.int_field4,
        int_field5=data_entry.int_field5,
        int_field6=data_entry.int_field6,
        int_field7=data_entry.int_field7,
        int_field8=data_entry.int_field8,
        owner_id=current_user.id
    )
    db.add(new_data_entry)
    db.commit()
    db.refresh(new_data_entry)

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"Created data entry with ID {new_data_entry.id}"
    )
    log_activity(db, activity_log, current_user.id)

    return schemas.ResponseModel(success=True, data=schemas.DataEntryResponse.from_orm(new_data_entry))

# Endpoint untuk mendapatkan semua data entry pengguna saat ini
@app.get("/data_entries/", response_model=schemas.ResponseModel)
def read_data_entries(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    data_entries = db.query(models.DataEntry).filter(models.DataEntry.owner_id == current_user.id).offset(skip).limit(limit).all()

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"Retrieved {len(data_entries)} data entries."
    )
    log_activity(db, activity_log, current_user.id)

    data_response = [schemas.DataEntryResponse.from_orm(entry) for entry in data_entries]
    return schemas.ResponseModel(success=True, data=data_response)

# Endpoint untuk mendapatkan data entry spesifik
@app.get("/data_entries/{data_entry_id}", response_model=schemas.ResponseModel)
def read_data_entry(
    data_entry_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    data_entry = db.query(models.DataEntry).filter(
        models.DataEntry.id == data_entry_id,
        models.DataEntry.owner_id == current_user.id
    ).first()
    if data_entry is None:
        return schemas.ResponseModel(success=False, error="Data entry tidak ditemukan")

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"Retrieved data entry with ID {data_entry_id}"
    )
    log_activity(db, activity_log, current_user.id)

    return schemas.ResponseModel(success=True, data=schemas.DataEntryResponse.from_orm(data_entry))

# Endpoint untuk memperbarui data entry
@app.put("/data_entries/{data_entry_id}", response_model=schemas.ResponseModel)
def update_data_entry(
    data_entry_id: int,
    data_entry: schemas.DataEntryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_data_entry = db.query(models.DataEntry).filter(
        models.DataEntry.id == data_entry_id,
        models.DataEntry.owner_id == current_user.id
    ).first()
    if db_data_entry is None:
        return schemas.ResponseModel(success=False, error="Data entry tidak ditemukan")
    
    # Update field jika diberikan
    for field, value in data_entry.dict(exclude_unset=True).items():
        setattr(db_data_entry, field, value)
    
    db.commit()
    db.refresh(db_data_entry)

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"Updated data entry with ID {data_entry_id}"
    )
    log_activity(db, activity_log, current_user.id)

    return schemas.ResponseModel(success=True, data=schemas.DataEntryResponse.from_orm(db_data_entry))
@app.delete("/data_entries/{data_entry_id}", response_model=schemas.ResponseModel, status_code=status.HTTP_200_OK)
def delete_data_entry(
    data_entry_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    db_data_entry = db.query(models.DataEntry).filter(
        models.DataEntry.id == data_entry_id,
        models.DataEntry.owner_id == current_user.id
    ).first()
    if db_data_entry is None:
        return schemas.ResponseModel(success=False, error="Data entry tidak ditemukan")
    db.delete(db_data_entry)
    db.commit()

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"Deleted data entry with ID {data_entry_id}"
    )
    log_activity(db, activity_log, current_user.id)

    return schemas.ResponseModel(success=True, data=None)

# Endpoint untuk membuat log aktivitas (opsional, jika ingin membuat log secara manual)
@app.post("/logs/", response_model=schemas.ResponseModel)
def create_activity_log(
    log: schemas.ActivityLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    created_log = log_activity(db, log, current_user.id)
    return schemas.ResponseModel(success=True, data=schemas.ActivityLogResponse.from_orm(created_log))

# Endpoint untuk membaca log aktivitas pengguna
@app.get("/logs/", response_model=schemas.ResponseModel)
def read_activity_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    logs = db.query(models.ActivityLog)\
             .filter(models.ActivityLog.user_id == current_user.id)\
             .order_by(models.ActivityLog.timestamp.desc())\
             .offset(skip).limit(limit).all()

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"Retrieved {len(logs)} activity logs."
    )
    log_activity(db, activity_log, current_user.id)

    logs_response = [schemas.ActivityLogResponse.from_orm(log) for log in logs]
    return schemas.ResponseModel(success=True, data=logs_response)
