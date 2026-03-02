#!/bin/sh
set -e

echo "Ejecutando migraciones …"
python manage.py migrate --noinput

echo "Collectstatic …"
python manage.py collectstatic --noinput 2>/dev/null || true

echo "Iniciando servidor …"
exec gunicorn config.asgi:application \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -
