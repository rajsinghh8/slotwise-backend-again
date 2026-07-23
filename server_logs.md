# Server Logs [Iteration 0]

## Platform - OS + python version
- OS: linux
- Python: 3.11.2

## Database
- Original URLs : postgresql+asyncpg://myuser:mypassword@db:5432/gen_6ea131cada; postgresql+asyncpg://myuser:mypassword@localhost:5432/gen_6ea131cada
- Resolved URLs : postgresql+asyncpg://myuser:mypassword@localhost:5432/gen_319b511664; postgresql+asyncpg://myuser:mypassword@localhost:5432/gen_6ea131cada
- Env file      : .env_a6b2546857a5b043

## Start Script - which script was used
- start.sh (PORT=41553)

## Files Generated / Modified
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/.env_a6b2546857a5b043 - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/main.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/core/auth.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/core/security.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/database.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/models.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/schemas.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/numbers.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/appointments.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/auth.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/availability.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/dashboard.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/locations.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/services.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/slots.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/staff.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/waitlist.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/services/slots.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/services/waitlist.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/seed.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/tests/conftest.py - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/docker-compose.yml - OK
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/start.sh - OK

## API Test Results

| Method | Path | Status | HTTP Code | Notes |
|---|---|---:|---:|---|
| GET | /health | PASSED | 200 | Health check OK |
| POST | /add | PASSED | 201 | Adds number, duplicate returns message |
| POST | /api/v1/auth/register | PASSED | 201 | User registration |
| POST | /api/v1/auth/login | PASSED | 200 | Token issued |
| GET | /api/v1/auth/me | PASSED | 200 | Authenticated profile |
| GET | /api/v1/auth/me | PASSED | 401 | Missing/invalid token |
| POST | /api/v1/locations | PASSED | 201 | Create location |
| GET | /api/v1/locations | PASSED | 200 | List locations |
| GET | /api/v1/locations/{id} | PASSED | 200 | Get location |
| PUT | /api/v1/locations/{id} | PASSED | 200 | Update location |
| DELETE | /api/v1/locations/{id} | PASSED | 204 | Delete location |
| POST | /api/v1/services | PASSED | 201 | Create service |
| GET | /api/v1/services | PASSED | 200 | List services |
| GET | /api/v1/services/{id} | PASSED | 200 | Get service |
| PUT | /api/v1/services/{id} | PASSED | 200 | Update service |
| DELETE | /api/v1/services/{id} | PASSED | 204 | Delete service |
| POST | /api/v1/staff | PASSED | 201 | Create staff profile |
| GET | /api/v1/staff | PASSED | 200 | List staff |
| GET | /api/v1/staff/{id} | PASSED | 200 | Get staff profile |
| POST | /api/v1/staff/{id}/services | PASSED | 201 | Assign staff service |
| GET | /api/v1/staff/{id}/services | PASSED | 200 | List staff services |
| POST | /api/v1/staff/{id}/schedules | PASSED | 201 | Create schedule |
| GET | /api/v1/staff/{id}/schedules | PASSED | 200 | List schedules |
| POST | /api/v1/staff/{id}/overrides | PASSED | 201 | Create override |
| GET | /api/v1/staff/{id}/overrides | PASSED | 200 | List overrides |
| GET | /api/v1/slots | PASSED | 200 | Get available slots |
| POST | /api/v1/appointments | PASSED | 201 | Create appointment |
| GET | /api/v1/appointments | PASSED | 200 | List appointments |
| GET | /api/v1/appointments/{id} | PASSED | 200 | Get appointment |
| POST | /api/v1/appointments/{id}/cancel | PASSED | 200 | Cancel appointment |
| POST | /api/v1/appointments/{id}/status | PASSED | 422 | Reject premature completion |
| GET | /api/v1/waitlist | PASSED | 200 | List waitlist |
| POST | /api/v1/waitlist | PASSED | 201 | Join waitlist |
| DELETE | /api/v1/waitlist/{id} | PASSED | 204 | Leave waitlist |
| GET | /api/v1/dashboard | PASSED | 200 | Manager dashboard |

## Errors Fixed This Iteration
1. /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/start.sh -> hardcoded port 40119 -> use PORT env with 41553 default

## Still Failing
- None

