#!/usr/bin/env bash
set -e

exec celery -A config worker -l info
