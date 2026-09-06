.PHONY: dev debug check test lint fix-ruff run

run:
	uv run --env-file .env fastapi dev app/main.py

dev:
	uv run --env-file .env fastapi dev --no-reload app/main.py

debug:
	uv run --env-file .env python -m debugpy --listen 127.0.0.1:5678 -m uvicorn app.main:app --port 8000

lint:
	uv run ruff check .
	uv run basedpyright

fix-ruff:
	uv run ruff check --fix . && uv run ruff format .

test:
	uv run pytest -s
