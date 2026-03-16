from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Habit, HabitEntry
from app.schemas import HabitCreate, HabitResponse, HabitEntryCreate, HabitEntryResponse
from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user_from_cookie
from datetime import date

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/habits", tags=["habits"])


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

    habits = (
        db.query(Habit)
        .filter(Habit.user_id == current_user.id)
        .order_by(Habit.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "partials/habits_list.html",
        {
            "request": request,
            "habits": habits,
        },
    )


@router.post("/web/habits/{habit_id}/toggle-today", response_class=HTMLResponse)
def web_toggle_habit_today(
    habit_id: int,
    request: Request,
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
        "partials/habits_list.html",
        {
            "request": request,
            "habits": habits,
            "completed_today_ids": completed_today_ids,
            "today": today,
        },
    )
