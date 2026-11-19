#!/bin/sh
# Fail startup if migrations or static collection fail; never mask errors.
set -eu
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
