#!/bin/sh
set -e

echo "Ejecutando migraciones …"
python manage.py migrate --noinput

python manage.py restore_db

echo "Collectstatic …"
python manage.py collectstatic --noinput 2>/dev/null || true

echo "Iniciando servidor …"
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile -
