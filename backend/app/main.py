from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from app.database import engine, Base
from app.models import User, Habit, HabitEntry
from app.routers.auth import router as auth_router
from app.routers.habits import router as habits_router
from app.routers.stats import router as stats_router
from fastapi import FastAPI, Request, Depends
from app.dependencies import get_current_user_from_cookie
from app.models import User, Habit, HabitEntry
from datetime import date
from app.models import HabitEntry

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth_router)
app.include_router(habits_router)
app.include_router(stats_router)


@app.get("/", response_class=HTMLResponse)
def read_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/db-test")
def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {"message": "Database connection successful", "result": value}


@app.get("/auth-page", response_class=HTMLResponse)
def auth_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request, current_user: User = Depends(get_current_user_from_cookie)
):
    from datetime import date
    from app.database import SessionLocal
    from app.models import Habit, HabitEntry

    db = SessionLocal()
    try:
        today = date.today()

        habits = (
            db.query(Habit)
            .filter(Habit.user_id == current_user.id)
            .order_by(Habit.created_at.desc())
            .all()
        )

        completed_today_ids = {
            entry.habit_id
            for entry in db.query(HabitEntry)
            .join(Habit, Habit.id == HabitEntry.habit_id)
            .filter(
                Habit.user_id == current_user.id,
                HabitEntry.date == today,
                HabitEntry.completed == True,
            )
            .all()
        }

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "current_user": current_user,
                "habits": habits,
                "completed_today_ids": completed_today_ids,
                "today": today,
            },
        )
    finally:
        db.close()
