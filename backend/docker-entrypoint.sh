#!/bin/sh
set -eu

if [ "${AFROLETE_RUN_MIGRATIONS:-1}" = "1" ]; then
  alembic upgrade head
fi

if [ "${AFROLETE_SEED_DEMO:-0}" = "1" ]; then
  python -m app.demo_seed
fi

exec "$@"
