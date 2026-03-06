#!/bin/sh
set -e

DUMP_FILE="/docker-entrypoint-initdb.d/brfn_seed.dump"

if [ ! -f "$DUMP_FILE" ]; then
  echo "[db-init] Seed dump not found at $DUMP_FILE - skipping restore."
  exit 0
fi

echo "[db-init] Restoring seed data from $DUMP_FILE into $POSTGRES_DB..."
pg_restore \
  --username="$POSTGRES_USER" \
  --dbname="$POSTGRES_DB" \
  --no-owner \
  --no-privileges \
  "$DUMP_FILE"

echo "[db-init] Seed restore completed successfully."