#!/bin/sh
set -e

# Migrations are applied by the `backend` (API) service's entrypoint; this
# just waits for the DB to accept connections before starting the worker/beat
# process so it doesn't crash-loop during first-time startup.
python - <<'PYEOF'
import os
import sys
import time

import psycopg2

for attempt in range(30):
    try:
        psycopg2.connect(
            dbname=os.environ.get("POSTGRES_DB", "pixelforge"),
            user=os.environ.get("POSTGRES_USER", "pixelforge"),
            password=os.environ.get("POSTGRES_PASSWORD", "pixelforge"),
            host=os.environ.get("POSTGRES_HOST", "db"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
        ).close()
        print("Database is ready.")
        sys.exit(0)
    except psycopg2.OperationalError:
        print(f"Database not ready yet (attempt {attempt + 1}/30)...")
        time.sleep(2)

print("Database never became ready.", file=sys.stderr)
sys.exit(1)
PYEOF

exec "$@"
