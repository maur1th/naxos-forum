FROM python:3.6-alpine

MAINTAINER thomas@maurin.io
ENV HOME=/app \
    WORKERS=2

RUN set -ex \
        && apk add --no-cache \
                libpq \
                libmemcached \
                libjpeg-turbo \
        && pip3 install --upgrade --no-cache-dir pip

WORKDIR $HOME

COPY . $HOME
RUN set -ex \
        && apk add --no-cache --virtual .build-deps \
                musl-dev \
                gcc \
                postgresql-dev \
                libmemcached-dev \
                libjpeg-turbo-dev \
                libwebp-dev \
                zlib-dev \
                cyrus-sasl-dev \
        && pip3 install --no-cache-dir -r requirements.txt \
        && apk del .build-deps

RUN adduser -D -s /bin/false app
RUN chown -R app:app $HOME/*
USER app
CMD gunicorn naxos.wsgi:application -w $WORKERS -b :8000
