#!/usr/bin/env bash
set -e


celery -A config worker -l info \
  --concurrency=2 \
  --without-gossip \
  --without-mingle \
  --without-heartbeat
