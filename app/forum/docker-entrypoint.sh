#!/bin/sh
python3 manage.py migrate

echo Starting Gunicorn.
exec gunicorn naxos.wsgi:application \
    --workers $WORKERS \
    --bind :5000
