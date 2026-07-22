# Makefile for SlotWise development tasks
.PHONY: help install start test seed docker-up docker-down lint format

help:
	@echo "SlotWise Makefile targets:"
	@echo "  install    - Install Python dependencies"
	@echo "  start      - Start the development server on port 40119"
	@echo "  test       - Run the test suite"
	@echo "  seed       - Seed the database with sample data"
	@echo "  docker-up  - Start services with Docker Compose"
	@echo "  docker-down - Stop Docker Compose services"

install:
	pip install -r requirements.txt

start:
	chmod +x start.sh && PORT=40119 bash start.sh

test:
	pytest tests/ -v --tb=short

seed:
	python3 seed.py

docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
