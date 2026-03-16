from pydantic import BaseModel
from datetime import datetime


class HabitCreate(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    frequency: str = "daily"


class HabitResponse(BaseModel):
    id: int
    title: str
    description: str | None
    category: str | None
    frequency: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True