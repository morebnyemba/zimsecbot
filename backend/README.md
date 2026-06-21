# ZIMSEC STEM Revision Platform — Backend

Django + DRF backend. See `../docs/` for architecture, database, API, WhatsApp flow, AI, and monetization design docs.

## Local development

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

This starts Postgres (with `pgvector`), Redis, the Django dev server (`:8000`), a Celery worker, and Celery beat.

Run migrations and create an admin user:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

## Without Docker

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env  # point DATABASE_URL/REDIS_URL at local services
python manage.py migrate
python manage.py runserver
```

## Tests & lint

```bash
pytest
ruff check .
```

API docs (once running): `http://localhost:8000/api/docs/`.
