# app/main.py

from fastapi import FastAPI, Depends, HTTPException, status, Request
from typing import List
from . import models, schemas, auth
from .database import engine
from sqlalchemy.orm import Session
from .dependencies import get_db
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Buat semua tabel di database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Management API")

# Custom Exception Handler untuk ValidationError
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    errors = exc.errors()
    formatted_errors = []
    for error in errors:
        field = " -> ".join([str(loc) for loc in error['loc']])
        msg = error['msg']
        formatted_errors.append({"field": field, "message": msg})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": formatted_errors},
    )

# Endpoint Registrasi Pengguna Baru
@app.post("/register/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Validasi role (contoh: hanya 1 atau 2 yang diizinkan)
    if user.role not in [1, 2]:
        raise HTTPException(status_code=400, detail="Role tidak valid")
    
    # Cek apakah username sudah ada
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username sudah terdaftar")
    
    # Cek apakah email sudah ada
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

# Endpoint Login menggunakan OAuth2 Password Request Form (tidak digunakan dalam pendekatan ini)
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

# Endpoint Login menggunakan JSON
@app.post("/login/", response_model=schemas.Token)
def login_user_json(login: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, login.username, login.password)
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

# Endpoint POST Terproteksi: Membuat Postingan Baru dengan Token dalam Body JSON
@app.post("/posts/", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: schemas.PostCreateWithToken, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user_body)):
    new_post = models.Post(
        title=post.title,
        content=post.content,
        published=post.published,
        owner_id=current_user.id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

# Endpoint GET Terproteksi: Mendapatkan Data Pengguna Saat Ini dengan Token dalam Body JSON
@app.post("/users/me/", response_model=schemas.UserResponse)
def read_users_me(request: schemas.PostCreateWithToken, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user_body)):
    return current_user
