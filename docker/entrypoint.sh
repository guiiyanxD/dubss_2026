#!/bin/sh
set -e

echo "Esperando a PostgreSQL en ${POSTGRES_HOST}:${POSTGRES_PORT}..."

python -c "
import sys, time, os
try:
    import psycopg
except ImportError:
    import psycopg2 as psycopg

retries = 30
while retries > 0:
    try:
        conn = psycopg.connect(
            host=os.environ.get('POSTGRES_HOST', 'db'),
            port=int(os.environ.get('POSTGRES_PORT', 5432)),
            dbname=os.environ.get('POSTGRES_DB', 'becas_db'),
            user=os.environ.get('POSTGRES_USER', 'becas_user'),
            password=os.environ.get('POSTGRES_PASSWORD', ''),
        )
        conn.close()
        break
    except Exception as e:
        retries -= 1
        if retries == 0:
            print(f'No se pudo conectar a PostgreSQL: {e}')
            sys.exit(1)
        time.sleep(1)
"

echo "PostgreSQL disponible."

exec "$@"
