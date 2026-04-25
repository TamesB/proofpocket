# ProofPocket

Django + TailwindCSS + HTMX “SPA-like” app to store receipts/warranties and get scheduled **email reminders** (Resend + Celery + Redis).

## Requirements
- Python 3.13+
- Node 18+ (you have Node installed)
- Docker (for Redis) or a local Redis instance

## Setup

### 1) Python deps

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 2) Environment variables
- Copy `.env.example` → `.env`
- Set `RESEND_API_KEY`

### 3) Tailwind build

```powershell
npm install
npm run tailwind:build
```

For watch mode:

```powershell
npm run tailwind:watch
```

### 4) Database

```powershell
.\.venv\Scripts\python manage.py migrate
```

### 5) Redis (Docker)

```powershell
docker compose up -d
```

## Run

### Django

```powershell
.\.venv\Scripts\python manage.py runserver
```

Open `http://127.0.0.1:8000/` and sign up.

### Celery worker

```powershell
.\.venv\Scripts\celery -A config worker -l info
```

### Celery beat (scheduler)

```powershell
.\.venv\Scripts\celery -A config beat -l info
```

## How reminders work (MVP)
- When you create/edit a purchase, `reminders.services.recompute_events_for_purchase()` creates `ReminderEvent` rows from your `ReminderRule`s.\n- Celery Beat runs every 60 seconds to enqueue due events.\n- Celery Worker sends via Resend and marks events `sent/failed/skipped`.\n+
## Notes
- Dev DB is SQLite.\n- File uploads go to `media/`.\n
## Deploy to Railway
1) Push this repo to GitHub.
2) In Railway: **New Project → Deploy from GitHub Repo**.
3) Add services:
   - **PostgreSQL** (Railway will provide `DATABASE_URL`)
   - **Redis** (set `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` from the Redis URL)
4) Set variables:
   - `DJANGO_SECRET_KEY`
   - `DJANGO_DEBUG=0`
   - `RESEND_API_KEY`
   - `DEFAULT_FROM_EMAIL`

This repo includes `railway.toml`, which runs migrations + collectstatic on deploy and starts Gunicorn.
