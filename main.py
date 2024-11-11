# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from . import models, schemas, auth
from .database import engine
from sqlalchemy.orm import Session
from .dependencies import get_db
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

# Buat semua tabel di database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Management API")

@app.post("/register/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Cek apakah username atau email sudah ada
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username sudah terdaftar")
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email sudah terdaftar")
    
    # Hash password
    hashed_password = auth.get_password_hash(user.password)
    
    # Buat pengguna baru
    new_user = models.User(
        name=user.name,
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        disease=user.disease,
        date_of_birth=user.date_of_birth,
        place_of_birth=user.place_of_birth
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return user
