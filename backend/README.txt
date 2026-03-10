Окружение и запуск backend

  python -m venv .venv
  source .venv/bin/activate   # Linux/macOS
  pip install -e ".[dev]"
  cp .env.example .env

  # В .env задать DATABASE_URL с реальным пользователем и паролем PostgreSQL.
  # Создать БД и пользователя (в psql или pgAdmin):
  #   CREATE USER library_user WITH PASSWORD 'your_password';
  #   CREATE DATABASE library OWNER library_user;
  # Затем: DATABASE_URL=postgresql+asyncpg://library_user:your_password@localhost:5432/library

  alembic upgrade head
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Линтинг: ruff check . && ruff format --check .
