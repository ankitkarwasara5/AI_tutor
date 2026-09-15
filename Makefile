.PHONY: install dev test lint run docker-build docker-run

install:
	python -m pip install -r requirements.txt

dev:
	python -m pip install -r requirements-dev.txt

test:
	pytest

lint:
	ruff check .
	ruff format --check .

run:
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

docker-build:
	docker build -t local-ai-learning-tutor .

docker-run:
	docker compose up --build
