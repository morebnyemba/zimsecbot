# Deployment Runbook

Scope: the Django backend (`backend/`). The Next.js admin (`frontend/`) and
student (`student-portal/`) apps are deployed separately (e.g. as their own
Coolify/Vercel services) and are not covered here.

## 1. Required environment variables

Copy `backend/.env.example` to `backend/.env` on the host and set production
values for at least:

| Variable | Notes |
|---|---|
| `DJANGO_SECRET_KEY` | Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | Must be `False` in production — enables HSTS/secure-cookie settings in `config/settings.py` |
| `ALLOWED_HOSTS` | Comma-separated production hostnames |
| `CORS_ALLOWED_ORIGINS` | Production frontend origins |
| `DATABASE_URL` | `postgres://zimsec:<password>@postgres:5432/zimsec` |
| `REDIS_URL`, `CELERY_BROKER_URL` | Point at the `redis` service |
| `GEMINI_API_KEY`, `WHATSAPP_*`, `PAYNOW_*` | Third-party credentials |
| `SENTRY_DSN` | Optional — leave blank to disable error tracking |
| `POSTGRES_PASSWORD` | Read by `docker-compose.prod.yml` for the `postgres` service |

`SENTRY_DSN`/`SENTRY_ENVIRONMENT`/`SENTRY_TRACES_SAMPLE_RATE` are read directly
by `config/settings.py`; everything else flows through `backend/.env`.

## 2. Deploying with Docker Compose

```bash
cp backend/.env.example backend/.env   # then edit with production values
docker compose -f docker-compose.prod.yml up -d --build
```

This brings up `postgres`, `redis`, `backend` (gunicorn, runs `migrate`
on boot), `celery_worker`, `celery_beat`, and an `nginx` reverse proxy on
port 80 serving `/static/` and `/media/` directly and proxying everything
else to gunicorn.

TLS termination is expected to happen upstream of `nginx` (Coolify's built-in
Traefik, or another load balancer) forwarding `X-Forwarded-Proto: https` —
`SECURE_PROXY_SSL_HEADER` in `config/settings.py` relies on that header to
know a request arrived over HTTPS.

### Coolify

Point a Coolify "Docker Compose" resource at `docker-compose.prod.yml`,
set the environment variables from section 1 in the Coolify UI (or mount
`backend/.env` as a secret), and let Coolify's proxy handle the public
domain/TLS in front of the `nginx` service's port 80.

## 3. Database migrations

The `backend` service runs `python manage.py migrate --noinput` on every
boot (see `command:` in `docker-compose.prod.yml`). For a one-off manual
migration (e.g. after a hotfix without a redeploy):

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

## 4. Health checks

- `GET /health/` — checks DB and cache connectivity, returns `200` (`{"status": "ok", ...}`)
  or `503`. Used by the Dockerfile `HEALTHCHECK` and safe to point an external
  uptime monitor or load-balancer probe at.
- `GET /metrics/` — Prometheus metrics (request latency/count, exceptions)
  exposed by `django-prometheus`. Scrape this from a Prometheus instance;
  it is not authenticated, so keep it off the public internet (block at the
  load balancer/firewall, or put it behind an internal-only route).

## 5. Observability

- **Errors**: set `SENTRY_DSN` to enable automatic exception capture for
  both Django and Celery (`config/settings.py`). Leave unset in
  staging/dev to no-op.
- **Logs**: structured to stdout/stderr (`LOGGING` in `config/settings.py`,
  level via `LOG_LEVEL`). Docker Compose / Coolify will collect these from
  the container log stream — no separate log shipping is configured yet.
- **Metrics**: `/metrics/` as above. No Prometheus/Grafana stack is
  provisioned by this repo — point an existing observability stack at it.

## 6. Rollback

```bash
docker compose -f docker-compose.prod.yml pull   # if using a registry-built image
# or: git checkout <previous-tag> && docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate <app> <previous_migration_name>  # only if the bad release added a migration that must be reverted
```

Prefer rolling back the application image first; only reverse a migration if
the new migration is itself the cause of the incident (Django migrations are
not automatically reversed by an image rollback).

## 7. On-call basics

1. Check `/health/` — if it's `503`, the next step is whichever check failed
   (`database` or `cache`); confirm `postgres`/`redis` containers are up.
2. Check Sentry (if enabled) for the most recent unhandled exception.
3. Check container logs: `docker compose -f docker-compose.prod.yml logs -f backend celery_worker`.
4. Celery queues are split by `CELERY_TASK_ROUTES` in `config/settings.py`
   (`whatsapp`, `ai`, `analytics`, `billing`, default) — if one feature area
   is stuck, check whether its queue's worker is consuming
   (`celery -A config inspect active`).
5. Paynow webhook failures show up as `403` responses from
   `apps.billing.views.PaynowWebhookView` (hash mismatch) — cross-check the
   `PAYNOW_INTEGRATION_KEY` env var against the Paynow merchant dashboard
   before assuming an attack.

## Known gaps (not yet built)

- No automated log shipping / centralized log aggregation.
- No Prometheus/Grafana/Alertmanager stack provisioned — `/metrics/` is
  exposed but unconsumed until an external stack scrapes it.
- No load/performance testing has been run against this configuration yet.
- No CD pipeline (CI runs lint/audit/tests only; deployment is manual via
  `docker compose ... up -d --build` or a Coolify webhook).
