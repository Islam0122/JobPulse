#!/usr/bin/env bash
set -e


celery -A config worker -l info --uid 1000 --without-gossip --without-mingle --without-heartbeat

