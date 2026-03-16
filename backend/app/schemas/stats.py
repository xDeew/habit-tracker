from pydantic import BaseModel


class HabitStatsResponse(BaseModel):
    habit_id: int
    title: str
    total_entries: int
    completed_entries: int
    completion_rate: float
    current_streak: int
    longest_streak: int