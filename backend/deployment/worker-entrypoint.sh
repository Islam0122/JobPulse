#!/usr/bin/env bash
set -e

export CELERY_ALLOW_ROOT=1

# Запуск worker
exec celery -A config worker -l info
