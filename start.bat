@echo off
REM Start script for SlotWise FastAPI backend (Windows)
set PORT=40119
set PYTHONUNBUFFERED=1

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt -q

echo Starting SlotWise on port %PORT%...
uvicorn app.main:app --host 0.0.0.0 --port 40119 --reload
