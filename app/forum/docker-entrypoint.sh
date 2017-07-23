#!/bin/sh
if [ $LOCAL_ENV -eq 1 ]; then
    python3 manage.py migrate
    python3 manage.py loaddata fixtures.json
    if [ $? -ne 0 ]; then
        python3 manage.py flush --noinput
        python3 manage.py loaddata fixtures.json
    fi
    python3 manage.py runserver 0.0.0.0:5000
else
    echo Starting Gunicorn.
    exec gunicorn naxos.wsgi:application \
        --workers $WORKERS \
        --bind :5000
fi
