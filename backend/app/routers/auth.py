from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserResponse
from app.security import hash_password, verify_password, create_access_token
from app.dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
import re

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


def validate_password_rules(password: str) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters long."

    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."

    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."

    if not re.search(r"\d", password):
        return "Password must contain at least one number."

    return None


@router.post("/signup", response_model=UserResponse)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(
        {"user_id": user.id, "email": user.email, "username": user.username}
    )

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }


@router.post("/web/signup", response_class=HTMLResponse)
def web_signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        return templates.TemplateResponse(
            "partials/auth_feedback.html",
            {
                "request": request,
                "error": "An account with this email already exists.",
                "success": None,
            },
            status_code=400,
        )

    password_error = validate_password_rules(password)

    if password_error:
        return templates.TemplateResponse(
            "partials/auth_feedback.html",
            {
                "request": request,
                "error": password_error,
                "success": None,
            },
            status_code=400,
        )

    new_user = User(
        username=username, email=email, hashed_password=hash_password(password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(
        {
            "user_id": new_user.id,
            "email": new_user.email,
            "username": new_user.username,
        }
    )

    response = HTMLResponse("")
    response.headers["HX-Redirect"] = "/dashboard"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60,
    )
    return response


@router.post("/web/login", response_class=HTMLResponse)
def web_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "partials/auth_feedback.html",
            {
                "request": request,
                "error": "Invalid email or password.",
                "success": None,
            },
            status_code=401,
        )

    token = create_access_token(
        {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
        }
    )

    response = HTMLResponse("")
    response.headers["HX-Redirect"] = "/dashboard"
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60,
    )
    return response


@router.post("/web/logout")
def web_logout():
    response = RedirectResponse(url="/auth-page", status_code=303)
    response.delete_cookie(key="access_token")
    return response
