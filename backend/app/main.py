from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from app.database import Base, engine
from app.dependencies import get_current_user_from_cookie
from app.models import User
from app.routers.auth import router as auth_router
from app.routers.habits import build_dashboard_context, router as habits_router
from app.routers.stats import router as stats_router

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
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        context = build_dashboard_context(db, current_user.id)

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "current_user": current_user,
                **context,
            },
        )
    finally:
        db.close()
