from fastapi import FastAPI
from sqlalchemy import text

from app.database import engine

app = FastAPI()


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