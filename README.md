# Job Application Tracker API

A REST API for tracking job applications, managing CV uploads, scheduling email reminders, and analysing your job search with dashboard analytics.

Built with **Django 6** · **Django REST Framework** · **PostgreSQL** · **Celery** 

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Quick Start — Docker](#quick-start--docker-recommended)
- [Quick Start — Local](#quick-start--local-virtualenv)
- [Environment Variables](#environment-variables)
- [Running the Services](#running-the-services)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [Useful Commands](#useful-commands)
- [Deployment](#deployment)

---

## Features

| Feature | Detail |
|---|---|
| **Authentication** | JWT (access + refresh tokens), token blacklist on logout |
| **Role-based access** | `job_seeker` (default) and `admin` roles |
| **Job application CRUD** | Full pipeline: Saved => Applied => Screening => Interview => Offer => Accepted/Rejected/Withdrawn |
| **Status history** | Immutable audit log of every status transition |
| **CV / document upload** | PDF, DOC, DOCX — validated extension + size (5 MB limit) |
| **Email reminders** | Scheduled via Celery Beat, fired per-minute, double-send protected |
| **Analytics dashboard** | Status breakdown, weekly/monthly volume, conversion funnel, stage duration, response rates, activity heatmap |
| **Search & filter** | Full-text search + multi-value filters on status, work mode, source, salary, date ranges |
| **Pagination** | Page-number pagination with rich metadata (total pages, has_next, etc.) |
| **RESTful API** | Versioned under `/api/v1/`, OpenAPI docs at `/api/docs/` |
| **Input validation** | Serializer-level + model-level, with clear error messages |

---

## Architecture

**4 Django apps, each owning a bounded domain:**

- `accounts` — users, JWT auth, roles, profiles
- `applications` — job applications, documents, status history
- `reminders` — scheduled email reminders via Celery
- `analytics` — read-only aggregation endpoints for dashboard charts

---

## Project Structure

```
jobtracker/
├── jobtracker/               # Django project package
│   ├── settings/
│   │   ├── base.py            # Shared settings
│   │   ├── dev.py             # Development overrides
│   │   └── prod.py            # Production hardening
│   ├── urls.py                # Root URL config (versioned /api/v1/)
│   ├── celery.py              # Celery app instance
│   └── wsgi.py
│
├── accounts/                  # Auth, JWT, roles, profiles
├── applications/              # Job CRUD, documents, status pipeline
├── reminders/                 # Email reminders + Celery tasks
├── analytics/                 # Dashboard aggregations
│
├── templates/
│   └── reminders/
│       ├── reminder_email.html
│       └── reminder_email.txt
│
├── tests/                     # Pytest test suite (one file per app)
│   ├── test_accounts.py
│   ├── test_applications.py
│   ├── test_reminders.py
│   └── test_analytics.py
│
├── requirements/
│   ├── base.txt               # Shared dependencies
│   ├── dev.txt                # + pytest, debug toolbar, ruff
│   └── prod.txt               # + gunicorn
│
├── .env.example               # All required environment variables documented
├── docker-compose.yml         # Full local dev stack
├── Dockerfile                 # Multi-stage production image
├── manage.py
└── pytest.ini
```

---

## Quick Start — Docker (Recommended)

The fastest path to a running system. Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/).

### 1. Clone and configure

```bash
git clone https://github.com/brandonkongwe/job-tracker-v1.git
cd jobtracker

# Copy the example env file and generate a secret key
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Paste the output as SECRET_KEY in .env
```

### 2. Start all services

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Django API** on port 8000 (runs migrations automatically)
- **Celery worker** (listens on `default` and `reminders` queues)
- **Celery Beat** (fires `dispatch_due_reminders` every minute)

### 3. Create a superuser

```bash
docker-compose exec api python manage.py createsuperuser
```

### 4. Verify it's working

```
API root:      http://localhost:8000/api/v1/
Swagger docs:  http://localhost:8000/api/docs/
ReDoc:         http://localhost:8000/api/redoc/
Django admin:  http://localhost:8000/admin/
```

---

## Quick Start — Local (Virtualenv)

Use this if you prefer running services natively or already have PostgreSQL and Redis installed.

### 1. Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Redis 7+

### 2. Clone and install

```bash
git clone https://github.com/brandonkongwe/job-tracker-v1.git
cd jobtracker

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements/dev.txt
```

### 3. Create the database

```bash
# Make sure PostgreSQL is running, then:
createdb job_tracker_db
```

### 4. Configure environment

```bash
cp .env.example .env
```

Open `.env` and update:

```env
SECRET_KEY=<generated-key>          # python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
DATABASE_URL=postgres://postgres:<your-pg-password>@localhost:5432/job_tracker_db
REDIS_URL=redis://localhost:6379/0
```

### 5. Run migrations and start

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 6. Start Celery (separate terminal windows)

```bash
# Terminal 2 — Celery worker
celery -A job_tracker worker -l info -Q default,reminders

# Terminal 3 — Celery Beat scheduler
celery -A job_tracker beat -l info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## Environment Variables

All variables are documented in `.env.example`. Key ones:

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | Django secret key — generate with `get_random_secret_key()` |
| `DEBUG` | — | `False` | Set `True` for development |
| `DATABASE_URL` | ✅ | — | PostgreSQL connection string |
| `CELERY_BROKER_URL` | ✅ | — | Redis URL for Celery broker |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | — | `60` | Access token TTL in minutes |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | — | `7` | Refresh token TTL in days |
| `EMAIL_BACKEND` | — | `console` | Use `console` in dev, configure SMTP for prod |
| `FRONTEND_URL` | — | `http://localhost:3000` | Used in reminder email links |
| `MAX_UPLOAD_SIZE` | — | `5242880` (5 MB) | CV upload size limit in bytes |

---

## Running the Services

### Django development server

```bash
python manage.py runserver
# or with explicit settings module:
DJANGO_SETTINGS_MODULE=job_tracker.settings.dev python manage.py runserver
```

### Celery worker

```bash
# Development — verbose, single worker
celery -A job_tracker worker -l info -Q default,reminders

# Production — multiple concurrent workers
celery -A job_tracker worker -l warning -Q default,reminders \
  --concurrency=4 --max-tasks-per-child=100
```

### Celery Beat

```bash
celery -A job_tracker beat -l info \
  --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Beat reads the schedule from the database (managed by `django-celery-beat`). The `dispatch_due_reminders` periodic task is auto-registered on first `migrate` via `RemindersConfig.ready()` — no manual setup needed.

### Triggering reminders manually (useful in dev)

```bash
# Fire the dispatch task immediately (bypasses the scheduler)
python manage.py shell -c "
from reminders.tasks import dispatch_due_reminders
result = dispatch_due_reminders.apply()
print(result.get())
"
```

---

## API Reference

Full interactive docs available at `/api/docs/` (Swagger UI) and `/api/redoc/` (ReDoc).

### Authentication

All endpoints except `register` and `login` require:
```
Authorization: Bearer <access_token>
```

#### Auth endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register/` | Create account |
| `POST` | `/api/v1/auth/login/` | Get access + refresh tokens |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh access token |
| `POST` | `/api/v1/auth/logout/` | Blacklist refresh token |
| `GET` | `/api/v1/auth/me/` | Get own profile |
| `PATCH` | `/api/v1/auth/me/` | Update own profile |
| `POST` | `/api/v1/auth/me/password/` | Change password |
| `GET` | `/api/v1/auth/users/` | List all users (admin only) |

#### Applications endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/applications/` | List own applications (paginated) |
| `POST` | `/api/v1/applications/` | Create application |
| `GET` | `/api/v1/applications/<id>/` | Get full detail |
| `PATCH` | `/api/v1/applications/<id>/` | Partial update (status, notes…) |
| `DELETE` | `/api/v1/applications/<id>/` | Delete application |
| `POST` | `/api/v1/applications/<id>/documents/` | Upload CV / cover letter |
| `DELETE` | `/api/v1/applications/<id>/documents/<doc_id>/` | Delete a document |
| `GET` | `/api/v1/applications/<id>/history/` | Status change audit trail |

**Query parameters for list:**

```
search=<term>               Full-text search (company, title, location, notes)
status=applied&status=interview   Filter by one or more statuses
work_mode=remote            Filter by work mode
is_active=true              Active applications only
applied_after=2024-01-01    Applied on or after date
salary_min_gte=50000        Minimum salary at least
ordering=-created_at        Sort (prefix - for descending)
page=2&page_size=10         Pagination
```

#### Reminders endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/reminders/` | List own reminders |
| `POST` | `/api/v1/reminders/` | Create reminder |
| `PATCH` | `/api/v1/reminders/<id>/` | Reschedule / update |
| `DELETE` | `/api/v1/reminders/<id>/` | Delete reminder |
| `POST` | `/api/v1/reminders/<id>/cancel/` | Cancel (deactivate) without deleting |

#### Analytics endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/analytics/dashboard/` | Full dashboard summary (single call) |
| `GET` | `/api/v1/analytics/status/` | Count per status |
| `GET` | `/api/v1/analytics/volume/weekly/` | Weekly volume (last 12 weeks) |
| `GET` | `/api/v1/analytics/volume/monthly/` | Monthly volume (last 12 months) |
| `GET` | `/api/v1/analytics/sources/` | Breakdown by discovery source |
| `GET` | `/api/v1/analytics/funnel/` | Stage conversion funnel |
| `GET` | `/api/v1/analytics/stage-duration/` | Avg days between stages |
| `GET` | `/api/v1/analytics/response-rate/` | Response, interview, offer rates |
| `GET` | `/api/v1/analytics/top-companies/` | Most applied-to companies |
| `GET` | `/api/v1/analytics/heatmap/` | Daily activity (365 days) |

### Example: Register and create an application

```bash
# 1. Register
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "first_name": "Brandon",
    "last_name": "Kongwe",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "SecurePass123!"}'
# → save the "access" token

# 3. Create an application
curl -X POST http://localhost:8000/api/v1/applications/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "First National Bank of Botswana",
    "job_title": "Data Engineer",
    "status": "applied",
    "applied_date": "2026-03-28",
    "source": "linkedin",
    "work_mode": "hybrid",
    "salary_min": 300000,
    "salary_max": 450000,
    "salary_currency": "BWP",
    "notes": "Applied via LinkedIn. Recruiter is Sarah M."
  }'

# 4. Upload a CV
curl -X POST http://localhost:8000/api/v1/applications/<app_id>/documents/ \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@/path/to/my_cv.pdf" \
  -F "document_type=cv"

# 5. Set a reminder
curl -X POST http://localhost:8000/api/v1/reminders/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "application": "<app_id>",
    "reminder_type": "follow_up",
    "remind_at": "2024-06-22T09:00:00Z",
    "message": "Send follow-up email to recruiter."
  }'

# 6. Check dashboard analytics
curl http://localhost:8000/api/v1/analytics/dashboard/ \
  -H "Authorization: Bearer <access_token>"
```

---

## Running Tests

```bash
# Run the full test suite
pytest

# With coverage report
pytest --cov=. --cov-report=term-missing

# Run a single app's tests
pytest tests/test_applications.py

# Run a single test class
pytest tests/test_analytics.py::TestConversionFunnel

# Run a single test
pytest tests/test_reminders.py::TestSendReminderEmailTask::test_double_send_protection

# Skip slow tests
pytest -m "not slow"

# Show output (useful for debugging task tests)
pytest -s tests/test_reminders.py
```

The test suite uses Django's test database and in-memory email backend — no real PostgreSQL, Redis, or SMTP credentials needed to run tests. Celery tasks run synchronously via `.apply()`.

---

## Useful Commands

```bash
# Generate a new secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Apply migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Generate OpenAPI schema to a file (useful for frontend codegen)
python manage.py spectacular --file schema.yml

# Check for missing migrations
python manage.py makemigrations --check

# Open Django shell
python manage.py shell

# Inspect the Celery Beat schedule
python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
for t in PeriodicTask.objects.all():
    print(t.name, '|', t.task, '|', t.enabled)
"

# Manually dispatch due reminders (dev testing)
python manage.py shell -c "
from reminders.tasks import dispatch_due_reminders
print(dispatch_due_reminders.apply().get())
"

# Lint the codebase
ruff check .

# Format the codebase
black .

# Run Docker services individually
docker-compose up db redis          # Infrastructure only
docker-compose up api               # API only (requires db + redis)
docker-compose logs -f celery_worker  # Tail worker logs
docker-compose exec api bash        # Shell into the API container
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 6.0, Django REST Framework 3.17 |
| Database | PostgreSQL 16 |
| Auth | JWT via `djangorestframework-simplejwt` |
| Task queue | Celery 5.6, Redis 7 |
| Scheduling | `django-celery-beat` |
| Filtering | `django-filter` |
| API docs | `drf-spectacular` (OpenAPI 3.1) |
| Testing | `pytest-django`, `factory-boy` |
| Linting | `ruff`, `black` |
| Production server | Gunicorn |
| Static files | Whitenoise |
| Containerisation | Docker, Docker Compose |