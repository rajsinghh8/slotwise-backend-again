# SlotWise — Appointment Booking Backend

A production-ready FastAPI backend for multi-location appointment booking businesses (salons, clinics, massage studios, etc.).

## Features

- **Multi-location support** with timezone-aware slot generation
- **Role-based access** (customer / staff / manager)
- **No double-booking** — enforced at DB level with row-locking
- **Smart availability** — weekly schedules + date-specific overrides
- **15-minute slot generation** in the location's local timezone
- **Cancellation rules** — 24h cutoff for customers, unrestricted for staff/managers
- **Waitlist** with FIFO notification on cancellation
- **Manager dashboard** with appointment statistics
- **Precise pricing** using NUMERIC(10,2)

## Tech Stack

- **FastAPI** — async Python web framework
- **SQLAlchemy 2.x async** — ORM with asyncpg driver
- **PostgreSQL** — primary database
- **Pydantic v2** — request/response validation
- **python-jose** — JWT authentication
- **passlib + bcrypt** — password hashing
- **pytz** — timezone conversion

## Project Structure

```
slotwise/
├── app/
│   ├── main.py              # FastAPI app + CORS + router registration
│   ├── database.py          # Async engine, session, Base
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic v2 schemas
│   ├── core/
│   │   ├── auth.py          # get_current_user dependency
│   │   └── security.py      # JWT + password hashing
│   ├── routers/
│   │   ├── auth.py          # POST /auth/register, /auth/login, GET /auth/me
│   │   ├── locations.py     # CRUD /locations
│   │   ├── services.py      # CRUD /services
│   │   ├── staff.py         # CRUD /staff + /staff/{id}/services
│   │   ├── availability.py  # /staff/{id}/schedules, /staff/{id}/overrides
│   │   ├── appointments.py  # /appointments (book, list, get, cancel, status)
│   │   ├── slots.py         # GET /slots (available booking slots)
│   │   ├── waitlist.py      # /waitlist (join, list, leave)
│   │   └── dashboard.py     # GET /dashboard (manager analytics)
│   └── services/
│       ├── slots.py         # Slot generation engine
│       └── waitlist.py      # Waitlist notification service
├── tests/
│   ├── conftest.py          # pytest fixtures (real DB, ASGI client)
│   ├── test_auth.py
│   ├── test_locations.py
│   ├── test_services.py
│   ├── test_staff.py
│   ├── test_availability.py
│   ├── test_appointments.py
│   ├── test_waitlist.py
│   └── test_slots.py
├── seed.py                  # Database seeder
├── requirements.txt
├── start.sh                 # Linux/macOS start script
├── start.bat                # Windows start script
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

## Setup

### Local Development

```bash
# 1. Clone and enter the project
cd slotwise

# 2. Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env_3698610c-0a42-47f4-8734-fc3a8dd320bd
# Edit the env file with your DATABASE_URL and SECRET_KEY

# 5. Start the server
chmod +x start.sh && bash start.sh
# Server runs at http://localhost:40119
```

### Docker

```bash
docker-compose up -d --build
# API: http://localhost:40119
# Docs: http://localhost:40119/docs
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection URL |
| `SECRET_KEY` | (set a strong key) | JWT signing secret |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token lifetime |
| `PORT` | `40119` | Server port |

## API Endpoints

### Authentication
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT |
| GET | `/api/v1/auth/me` | Get current user profile |
| PUT | `/api/v1/auth/me` | Update profile |

### Locations (manager write, all read)
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/locations` | Create location |
| GET | `/api/v1/locations` | List locations |
| GET | `/api/v1/locations/{id}` | Get location |
| PUT | `/api/v1/locations/{id}` | Update location |
| DELETE | `/api/v1/locations/{id}` | Soft-delete location |

### Services (manager write, all read)
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/services` | Create service |
| GET | `/api/v1/services` | List services |
| GET | `/api/v1/services/{id}` | Get service |
| PUT | `/api/v1/services/{id}` | Update service |
| DELETE | `/api/v1/services/{id}` | Soft-delete service |

### Staff
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/staff` | Create staff profile (manager) |
| GET | `/api/v1/staff` | List staff |
| GET | `/api/v1/staff/me` | Get own staff profile |
| GET | `/api/v1/staff/{id}` | Get staff profile |
| PUT | `/api/v1/staff/{id}` | Update staff profile |
| POST | `/api/v1/staff/{id}/services` | Assign service to staff (manager) |
| GET | `/api/v1/staff/{id}/services` | List staff services |
| DELETE | `/api/v1/staff/{id}/services/{svc_id}` | Remove service from staff (manager) |

### Availability
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/staff/{id}/schedules` | Add weekly schedule block |
| GET | `/api/v1/staff/{id}/schedules` | List weekly schedules |
| PUT | `/api/v1/staff/{id}/schedules/{sid}` | Update schedule block |
| DELETE | `/api/v1/staff/{id}/schedules/{sid}` | Delete schedule block |
| POST | `/api/v1/staff/{id}/overrides` | Add date override |
| GET | `/api/v1/staff/{id}/overrides` | List date overrides |
| DELETE | `/api/v1/staff/{id}/overrides/{oid}` | Delete date override |

### Slots
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/slots` | Get available slots for staff+service+date |

### Appointments
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/appointments` | Book appointment (customer) |
| POST | `/api/v1/appointments/manager` | Book on behalf of customer (manager) |
| GET | `/api/v1/appointments` | List appointments |
| GET | `/api/v1/appointments/{id}` | Get appointment |
| POST | `/api/v1/appointments/{id}/cancel` | Cancel appointment |
| POST | `/api/v1/appointments/{id}/status` | Update status (staff/manager) |

### Waitlist
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/waitlist` | Join waitlist |
| GET | `/api/v1/waitlist` | List waitlist entries |
| DELETE | `/api/v1/waitlist/{id}` | Leave waitlist |

### Dashboard
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/dashboard` | Appointment statistics (manager) |

## Running Tests

```bash
pytest tests/ -v --tb=short
```

## API Documentation

- Swagger UI: http://localhost:40119/docs
- ReDoc: http://localhost:40119/redoc
- Health: http://localhost:40119/health
