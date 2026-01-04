#!/bin/sh
set -e

# 1️⃣ Собираем статику
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 2️⃣ Миграции (только migrate, без makemigrations)
echo "Running migrations..."
python manage.py migrate --noinput

# 3️⃣ Создание суперпользователя (если нужно)
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')"

# 4️⃣ Запуск Gunicorn как PID 1
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --log-level info
