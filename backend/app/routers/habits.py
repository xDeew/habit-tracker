from datetime import date
from typing import Any, List

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_from_cookie
from app.dependencies import get_current_user
from app.models import Habit, HabitEntry, User
from app.schemas import (
    HabitCreate,
    HabitEntryCreate,
    HabitEntryResponse,
    HabitResponse,
)

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/habits", tags=["habits"])
VALID_HABIT_STATUSES = {"all", "open", "completed"}


def normalize_habit_status(value: str) -> str:
    return value if value in VALID_HABIT_STATUSES else "all"


def build_dashboard_context(
    db: Session,
    user_id: int,
    search: str = "",
    status: str = "all",
) -> dict[str, Any]:
    today = date.today()
    search_query = search.strip()
    status_filter = normalize_habit_status(status)

    habits = (
        db.query(Habit)
        .filter(Habit.user_id == user_id)
        .order_by(Habit.created_at.desc())
        .all()
    )

    completed_today_ids = {
        entry.habit_id
        for entry in db.query(HabitEntry)
        .join(Habit, Habit.id == HabitEntry.habit_id)
        .filter(
            Habit.user_id == user_id,
            HabitEntry.date == today,
            HabitEntry.completed == True,
        )
        .all()
    }

    filtered_habits = habits

    if search_query:
        normalized_query = search_query.lower()
        filtered_habits = [
            habit
            for habit in filtered_habits
            if normalized_query in habit.title.lower()
            or (habit.category and normalized_query in habit.category.lower())
            or (habit.description and normalized_query in habit.description.lower())
        ]

    if status_filter == "completed":
        filtered_habits = [
            habit for habit in filtered_habits if habit.id in completed_today_ids
        ]
    elif status_filter == "open":
        filtered_habits = [
            habit for habit in filtered_habits if habit.id not in completed_today_ids
        ]

    total_habits_count = len(habits)
    completed_count = len(completed_today_ids)
    open_count = max(total_habits_count - completed_count, 0)

    return {
        "habits": filtered_habits,
        "all_habits_count": total_habits_count,
        "matching_habits_count": len(filtered_habits),
        "completed_today_ids": completed_today_ids,
        "habit_search": search_query,
        "habit_status": status_filter,
        "habit_filter_counts": {
            "all": total_habits_count,
            "open": open_count,
            "completed": completed_count,
        },
        "today": today,
    }


@router.post("", response_model=HabitResponse)
def create_habit(
    habit_data: HabitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_habit = Habit(
        title=habit_data.title,
        description=habit_data.description,
        category=habit_data.category,
        frequency=habit_data.frequency,
        user_id=current_user.id,
    )

    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)

    return new_habit


@router.get("", response_model=List[HabitResponse])
def get_habits(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    habits = (
        db.query(Habit)
        .filter(Habit.user_id == current_user.id)
        .order_by(Habit.created_at.desc())
        .all()
    )

    return habits


@router.post("/{habit_id}/entries", response_model=HabitEntryResponse)
def create_or_update_habit_entry(
    habit_id: int,
    entry_data: HabitEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == current_user.id)
        .first()
    )

    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    existing_entry = (
        db.query(HabitEntry)
        .filter(HabitEntry.habit_id == habit_id, HabitEntry.date == entry_data.date)
        .first()
    )

    if existing_entry:
        existing_entry.completed = entry_data.completed
        existing_entry.note = entry_data.note
        db.commit()
        db.refresh(existing_entry)
        return existing_entry

    new_entry = HabitEntry(
        habit_id=habit_id,
        date=entry_data.date,
        completed=entry_data.completed,
        note=entry_data.note,
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return new_entry


@router.get("/{habit_id}/entries", response_model=List[HabitEntryResponse])
def get_habit_entries(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    return entries


@router.post("/web/habits/create", response_class=HTMLResponse)
def web_create_habit(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(""),
    frequency: str = Form("daily"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    new_habit = Habit(
        title=title,
        description=description or None,
        category=category or None,
        frequency=frequency,
        user_id=current_user.id,
    )

    db.add(new_habit)
    db.commit()

    context = build_dashboard_context(db, current_user.id)

    return templates.TemplateResponse(
        "partials/dashboard_updates.html",
        {
            "request": request,
            **context,
        },
    )


@router.get("/web/habits/list", response_class=HTMLResponse)
def web_habits_list(
    request: Request,
    search: str = "",
    status: str = "all",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    context = build_dashboard_context(db, current_user.id, search=search, status=status)

    return templates.TemplateResponse(
        "partials/dashboard_updates.html",
        {
            "request": request,
            **context,
        },
    )


@router.post("/web/habits/{habit_id}/toggle-today", response_class=HTMLResponse)
def web_toggle_habit_today(
    habit_id: int,
    request: Request,
    search: str = Form(""),
    status: str = Form("all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_cookie),
):
    today = date.today()

    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == current_user.id)
        .first()
    )

    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    existing_entry = (
        db.query(HabitEntry)
        .filter(HabitEntry.habit_id == habit_id, HabitEntry.date == today)
        .first()
    )

    if existing_entry:
        existing_entry.completed = not existing_entry.completed
    else:
        existing_entry = HabitEntry(
            habit_id=habit_id,
            date=today,
            completed=True,
            note=None,
        )
        db.add(existing_entry)

    db.commit()

    context = build_dashboard_context(
        db,
        current_user.id,
        search=search,
        status=status,
    )

    return templates.TemplateResponse(
        "partials/dashboard_updates.html",
        {
            "request": request,
            **context,
        },
    )
