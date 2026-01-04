#!/bin/sh
set -e

python manage.py collectstatic --noinput

python manage.py migrate --noinput

python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')"

python manage.py create_test_users

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --log-level info
