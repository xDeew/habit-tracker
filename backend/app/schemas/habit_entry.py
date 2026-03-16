from pydantic import BaseModel
from datetime import date, datetime


class HabitEntryCreate(BaseModel):
    date: date
    completed: bool = True
    note: str | None = None


class HabitEntryResponse(BaseModel):
    id: int
    date: date
    completed: bool
    note: str | None
    created_at: datetime

    class Config:
        from_attributes = True
