#!/usr/bin/env bash
# Start script for SlotWise FastAPI backend
set -e

# Hardcoded port — always use 40119
PORT=40119

export PYTHONUNBUFFERED=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Start the server
echo "Starting SlotWise on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port 40119 --reload
