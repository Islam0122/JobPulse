#!/usr/bin/env bash
set -e

celery -A config worker -l info --without-gossip --without-mingle --without-heartbeat
