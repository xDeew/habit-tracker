from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse
from app.security import hash_password, verify_password, create_access_token
from app.dependencies import get_current_user

app = FastAPI()

Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"message": "Habit Tracker API is running"}


@app.get("/db-test")
def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "message": "Database connection successful",
        "result": value
    }


@app.post("/auth/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/auth/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({
        "user_id": user.id,
        "email": user.email,
        "username": user.username
    })

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
    }


@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email
    }