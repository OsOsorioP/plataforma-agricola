from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import db_models
from app.db.database import get_db
from app.auth import create_access_token, verify_password, get_password_hash
from app.models.user import UserBase, UserCreate

router = APIRouter()

@router.post("/login")
def login_for_access_token(user_data: UserBase, db: Session = Depends(get_db)):
    user = db.query(db_models.User).filter(db_models.User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id, "username": user.full_name})
    return {"token": access_token, "token_type": "bearer"}

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user_exists = db.query(db_models.User).filter(db_models.User.email == user_data.email).first()
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    hashed_password = get_password_hash(user_data.password)
    new_user = db_models.User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        avatar=user_data.avatar
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token = create_access_token(data={"sub": new_user.email, "user_id": new_user.id, "username": new_user.full_name})
    return {"token": access_token, "token_type": "bearer"}