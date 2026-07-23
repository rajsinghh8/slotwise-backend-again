COMMIT_MESSAGE: Add duplicate-safe /add endpoint and update env configuration
## Features Added
- Added /add endpoint backed by a numbers table to prevent duplicate inserts and return a friendly message when already present.
- Added number schemas for request/response handling.
- Updated start.sh to honor PORT=41553 for consistent server startup.

## Files Modified
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/main.py — include numbers router and new env file
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/core/auth.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/core/security.py — env file update, remove hardcoded secret default
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/database.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/models.py — added NumberEntry model and env update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/schemas.py — added NumberCreate/NumberOut schemas and env update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/appointments.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/auth.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/availability.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/dashboard.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/locations.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/services.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/slots.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/staff.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/waitlist.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/services/slots.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/services/waitlist.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/seed.py — env file update
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/tests/conftest.py — updated fixtures to required pattern and env file
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/docker-compose.yml — updated DB URL
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/start.sh — use PORT env default 41553

## Files Added
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/.env_a6b2546857a5b043 — environment variables for runtime
- /home/ryzen/fast_api_generator_backend/repos/a6b2546857a5b043/app/routers/numbers.py — /add endpoint implementation

## Secrets Extracted
- SECRET_KEY -> written to .env_a6b2546857a5b043

## DB URLs Resolved
- postgresql+asyncpg://myuser:mypassword@db:5432/gen_6ea131cada -> postgresql+asyncpg://myuser:mypassword@localhost:5432/gen_319b511664
- postgresql+asyncpg://myuser:mypassword@localhost:5432/gen_6ea131cada -> postgresql+asyncpg://myuser:mypassword@localhost:5432/gen_6ea131cada

## Test Results Summary
- 53 PASSED, 0 FAILED, 0 SKIPPED
