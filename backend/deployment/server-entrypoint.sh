#!/bin/sh
set -e

echo "=== Starting entrypoint ==="

# 1️⃣ Сбор статики
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 2️⃣ Проверка базы и миграции с ограничением попыток
if [ "$RUN_MIGRATIONS" = "True" ]; then
    echo "Running migrations..."
    ATTEMPTS=0
    MAX_ATTEMPTS=10
    until python manage.py migrate || [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; do
        ATTEMPTS=$((ATTEMPTS+1))
        echo "Waiting for DB to be ready... ($ATTEMPTS/$MAX_ATTEMPTS)"
        sleep 3
    done

    if [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; then
        echo "⚠️ Database not ready after $MAX_ATTEMPTS attempts, exiting."
        exit 1
    fi
fi

# 3️⃣ Запуск сервера
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --log-level info \
    --forwarded-allow-ips "*" \
    --workers 3
