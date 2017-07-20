FROM python:3.6-alpine AS builder
COPY requirements* /
RUN apk add --no-cache \
        build-base \
        postgresql-dev \
        libmemcached-dev \
        libjpeg-turbo-dev \
        libwebp-dev \
        zlib-dev \
        cyrus-sasl-dev
ARG LOCAL_ENV=0
RUN if [ $LOCAL_ENV -eq 1 ]; \
    then \
        pip3 install -r requirements-dev.txt --target /packages; \
    else \
        pip3 install -r requirements-prd.txt --target /packages; \
    fi

FROM python:3.6-alpine
MAINTAINER thomas@maurin.io
ENV HOME=/app \
    PYTHONPATH=/packages \
    WORKERS=2
RUN apk add --no-cache \
        libpq \
        libmemcached \
        libjpeg-turbo
COPY --from=builder /packages /packages
COPY bin/gunicorn /usr/local/bin/gunicorn
COPY . $HOME
WORKDIR $HOME

EXPOSE 5000
ENTRYPOINT ["/bin/sh", "docker-entrypoint.sh"]
