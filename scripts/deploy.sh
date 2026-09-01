#!/usr/bin/env bash
#
# Zimfundi (zimsecbot backend) — deploy the current branch with a health gate
# and a rollback path.
#
# On 2026-09-01, a DB-password fix was applied with `docker compose restart
# backend celery_worker celery_beat` — which does NOT re-read a changed
# env_file, so the fix silently did nothing and the same password-auth
# failure kept happening. Separately, nginx crash-looped into "Restarting"
# for a stretch before anyone happened to run `docker ps` and notice. This
# builds first — while the old containers keep serving — and only swaps
# once the new images exist, gating the swap on the healthchecks now defined
# in docker-compose.prod.yml, so a broken swap is caught immediately instead
# of requiring live debugging.
#
# Usage:
#   ./scripts/deploy.sh            # pull, build, migrate, swap, verify
#   ./scripts/deploy.sh --no-pull  # deploy the working tree as-is
#
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

COMPOSE=(docker compose -f docker-compose.prod.yml)

PULL=1
[[ "${1:-}" == "--no-pull" ]] && PULL=0

say() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

# ── 1. Get the code ───────────────────────────────────────────────────────────
if [[ "$PULL" == "1" ]]; then
    say "Pulling"
    BEFORE="$(git rev-parse HEAD)"
    git pull --ff-only
    AFTER="$(git rev-parse HEAD)"
    [[ "$BEFORE" == "$AFTER" ]] && echo "    (already up to date)"
fi

# ── 2. Build BEFORE touching anything that is serving ─────────────────────────
say "Building images (site stays up)"
"${COMPOSE[@]}" build

# ── 3. Swap ───────────────────────────────────────────────────────────────────
# --wait blocks until every service's healthcheck passes (postgres, redis,
# backend, nginx), so a container that cannot actually answer — including one
# with a stale/wrong env_file value — is never left in place silently, unlike
# a plain `up -d` or `restart`. `python manage.py migrate` already runs as
# part of the backend container's own startup command, so no separate
# migrate step is needed here.
say "Starting new containers"
"${COMPOSE[@]}" up -d --wait --wait-timeout 120

# ── 4. Prove it ───────────────────────────────────────────────────────────────
# Verified from inside the nginx container itself (zimfundi_nginx publishes
# no host port — it's only reachable from bubi-rural's front nginx over the
# shared `edge` network), so this doesn't depend on that other stack being up.
say "Verifying"
code="$("${COMPOSE[@]}" exec -T nginx wget -qO- -S -T 5 http://127.0.0.1/health/ 2>&1 | awk '/HTTP\//{print $2; exit}')"
if [[ "$code" != "200" ]]; then
    echo "✗ Health check returned '${code:-no response}'."
    echo "  The previous images are still on this host — roll back with:"
    echo "    git reset --hard HEAD~1 && ./scripts/deploy.sh --no-pull"
    "${COMPOSE[@]}" logs --tail=40 backend nginx
    exit 1
fi

echo "✓ Healthy."
"${COMPOSE[@]}" ps --format 'table {{.Service}}\t{{.Status}}'

cat <<'NOTE'

Note: this only covers this stack's own health. It says nothing about
whether bubi-rural's front nginx is up or has TLS certs for the domains it
proxies here — check api.zimfundi.co.zw (and admin/portal once deployed)
separately if this reports healthy but the public site isn't reachable.
NOTE
