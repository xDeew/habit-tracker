from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Habit, HabitEntry
from app.schemas import HabitStatsResponse

router = APIRouter(tags=["stats"])


def calculate_streaks(entries):
    if not entries:
        return 0, 0

    completed_dates = sorted(
        [entry.date for entry in entries if entry.completed],
        reverse=True
    )

    if not completed_dates:
        return 0, 0

    longest_streak = 1
    current_streak = 1
    temp_streak = 1

    for i in range(len(completed_dates) - 1):
        diff = (completed_dates[i] - completed_dates[i + 1]).days

        if diff == 1:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        elif diff == 0:
            continue
        else:
            temp_streak = 1

    current_streak = 1
    for i in range(len(completed_dates) - 1):
        diff = (completed_dates[i] - completed_dates[i + 1]).days
        if diff == 1:
            current_streak += 1
        elif diff == 0:
            continue
        else:
            break

    return current_streak, longest_streak


@router.get("/habits/{habit_id}/stats", response_model=HabitStatsResponse)
def get_habit_stats(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == current_user.id)
        .first()
    )

    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    entries = (
        db.query(HabitEntry)
        .filter(HabitEntry.habit_id == habit_id)
        .order_by(HabitEntry.date.desc())
        .all()
    )

    total_entries = len(entries)
    completed_entries = len([entry for entry in entries if entry.completed])

    completion_rate = 0.0
    if total_entries > 0:
        completion_rate = round((completed_entries / total_entries) * 100, 2)

    current_streak, longest_streak = calculate_streaks(entries)

    return {
        "habit_id": habit.id,
        "title": habit.title,
        "total_entries": total_entries,
        "completed_entries": completed_entries,
        "completion_rate": completion_rate,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }


@router.get("/stats")
def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    habits = db.query(Habit).filter(Habit.user_id == current_user.id).all()
    habit_ids = [habit.id for habit in habits]

    entries = []
    if habit_ids:
        entries = db.query(HabitEntry).filter(HabitEntry.habit_id.in_(habit_ids)).all()

    total_habits = len(habits)
    total_entries = len(entries)
    completed_entries = len([entry for entry in entries if entry.completed])

    overall_completion_rate = 0.0
    if total_entries > 0:
        overall_completion_rate = round((completed_entries / total_entries) * 100, 2)

    return {
        "total_habits": total_habits,
        "total_entries": total_entries,
        "completed_entries": completed_entries,
        "overall_completion_rate": overall_completion_rate,
    }