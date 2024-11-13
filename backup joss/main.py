# app/main.py

from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from . import models, schemas, auth
from .database import engine
from sqlalchemy.orm import Session
from .dependencies import get_db
from .logging_service import log_activity
from datetime import timedelta

# Membuat semua tabel
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Management API")

# Endpoint untuk registrasi pengguna baru
@app.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Cek apakah username atau email sudah ada
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username atau email sudah digunakan")
    
    hashed_password = auth.get_password_hash(user.password)
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
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"User {db_user.username} telah mendaftar."
    )
    log_activity(db, activity_log, db_user.id)

    return db_user

# Endpoint untuk login
@app.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tidak valid username atau password",
            headers={"WWW-Authenticate": "Bearer"},
        )
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

    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint untuk mendapatkan informasi pengguna saat ini
@app.get("/users/me/", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# Endpoint untuk membuat data entry baru
@app.post("/data_entries/", response_model=schemas.DataEntryResponse)
def create_data_entry(
    data_entry: schemas.DataEntryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    new_data_entry = models.DataEntry(**data_entry.dict(), owner_id=current_user.id)
    db.add(new_data_entry)
    db.commit()
    db.refresh(new_data_entry)

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"Created data entry with ID {new_data_entry.id}"
    )
    log_activity(db, activity_log, current_user.id)

    return new_data_entry

# Endpoint untuk mendapatkan semua data entry pengguna saat ini
@app.get("/data_entries/", response_model=List[schemas.DataEntryResponse])
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

    return data_entries

# Endpoint untuk mendapatkan data entry spesifik
@app.get("/data_entries/{data_entry_id}", response_model=schemas.DataEntryResponse)
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
        raise HTTPException(status_code=404, detail="Data entry tidak ditemukan")

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"Retrieved data entry with ID {data_entry_id}"
    )
    log_activity(db, activity_log, current_user.id)

    return data_entry

# Endpoint untuk memperbarui data entry
@app.put("/data_entries/{data_entry_id}", response_model=schemas.DataEntryResponse)
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
        raise HTTPException(status_code=404, detail="Data entry tidak ditemukan")
    
    for key, value in data_entry.dict().items():
        setattr(db_data_entry, key, value)
    db.commit()
    db.refresh(db_data_entry)

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"Updated data entry with ID {data_entry_id}"
    )
    log_activity(db, activity_log, current_user.id)

    return db_data_entry

# Endpoint untuk menghapus data entry
@app.delete("/data_entries/{data_entry_id}", status_code=status.HTTP_204_NO_CONTENT)
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
        raise HTTPException(status_code=404, detail="Data entry tidak ditemukan")
    db.delete(db_data_entry)
    db.commit()

    # Log aktivitas
    activity_log = schemas.ActivityLogCreate(
        action=f"Deleted data entry with ID {data_entry_id}"
    )
    log_activity(db, activity_log, current_user.id)

    return None

# Endpoint untuk membuat log aktivitas (opsional, jika ingin membuat log secara manual)
@app.post("/logs/", response_model=schemas.ActivityLogResponse)
def create_activity_log(
    log: schemas.ActivityLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return log_activity(db, log, current_user.id)

# Endpoint untuk membaca log aktivitas pengguna
@app.get("/logs/", response_model=List[schemas.ActivityLogResponse])
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

    return logs
