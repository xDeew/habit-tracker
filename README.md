# Habit Tracker

A focused habit tracker built with FastAPI, Jinja templates, HTMX, and PostgreSQL.

The goal of the project is simple: keep habit tracking clear, calm, and fast. It is designed as a portfolio piece that shows both backend fundamentals and polished product thinking.

## What the app does

- Create an account and log in through a custom auth flow
- Create habits with title, description, category, and frequency
- Mark habits as completed for today
- See daily progress and completion summaries in the dashboard
- Filter habits by status and search across the list
- Delete habits when they were created by mistake
- Access JSON API endpoints alongside the server-rendered UI

## Stack

- FastAPI
- Jinja2 templates
- HTMX
- SQLAlchemy
- PostgreSQL
- Passlib + bcrypt
- JWT-based auth stored in an HTTP-only cookie for the web flow
- Custom CSS UI

## Current product surface

### Pages

- `/` - landing page
- `/auth-page` - login / sign up UI
- `/dashboard` - authenticated dashboard
- `/docs` - FastAPI Swagger docs

### API / web capabilities

- Auth API: signup, login, current user
- Web auth: signup, login, logout
- Habit API: create, list, delete
- Habit entries: create/update daily entries
- Stats endpoints for habit-level and user-level progress
- HTMX dashboard updates for:
  - creating habits
  - deleting habits
  - toggling completion
  - filtering/searching the habit list

## Project structure

```text
habit-tracker/
├─ backend/
│  ├─ app/
│  │  ├─ models/
│  │  ├─ routers/
│  │  ├─ schemas/
│  │  ├─ static/
│  │  │  └─ css/
│  │  ├─ templates/
│  │  │  └─ partials/
│  │  ├─ database.py
│  │  ├─ dependencies.py
│  │  ├─ main.py
│  │  └─ security.py
│  ├─ .env
│  ├─ main.py
│  └─ requirements.txt
└─ README.md
```

## Local setup

### 1. Create and activate a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Configure environment variables

Create `backend/.env` with values like:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/habit_tracker_db
JWT_SECRET=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
```

## Run the app

Start the server from the `backend` directory:

```bash
cd backend
uvicorn main:app --reload
```

Then open:

- `http://127.0.0.1:8000/`

## Notes

- The app currently creates database tables on startup through SQLAlchemy metadata.
- The web auth flow stores the access token in an HTTP-only cookie.
- The current setup is oriented toward local development and portfolio presentation.

## Why this project exists

This project is meant to demonstrate:

- practical FastAPI backend work
- server-rendered UI with HTMX interactions
- authentication and protected routes
- SQLAlchemy models and relational data
- product-minded frontend polish instead of only raw functionality

