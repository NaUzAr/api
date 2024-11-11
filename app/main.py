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

# Endpoint Login menggunakan OAuth2 Password Request Form (default)
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

# Endpoint POST Terproteksi: Membuat Postingan Baru
@app.post("/posts/", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
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

# Endpoint GET Terproteksi: Mendapatkan Semua Postingan Pengguna Saat Ini
@app.get("/posts/me", response_model=List[schemas.PostResponse])
def get_my_posts(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    posts = db.query(models.Post).filter(models.Post.owner_id == current_user.id).all()
    return posts

# Endpoint GET Terproteksi: Mendapatkan Data Pengguna Saat Ini
@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# Endpoint GET Terproteksi: Mendapatkan Data Pengguna Berdasarkan ID
@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: int, current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    return user

# Endpoint PUT Terproteksi: Mengupdate Postingan
@app.put("/posts/{post_id}", response_model=schemas.PostResponse)
def update_post(post_id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=404, detail="Post tidak ditemukan")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Tidak diizinkan mengupdate postingan orang lain")
    
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    db.refresh(post)
    return post

# Endpoint DELETE Terproteksi: Menghapus Postingan
@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()

    if post is None:
        raise HTTPException(status_code=404, detail="Post tidak ditemukan")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Tidak diizinkan menghapus postingan orang lain")
    
    post_query.delete(synchronize_session=False)
    db.commit()
    return
