FROM python:3.9-alpine AS builder
ARG LOCAL_ENV
RUN apk add --no-cache \
        build-base \
        postgresql-dev \
        libmemcached-dev \
        libjpeg-turbo-dev \
        libwebp-dev \
        zlib-dev \
        cyrus-sasl-dev
COPY requirements* /
RUN if [ $LOCAL_ENV -eq 1 ]; then \
        pip3 install -r requirements-dev.txt --target /packages; \
    else \
        pip3 install -r requirements.txt --target /packages; \
    fi

FROM python:3.9-alpine
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

ARG LOCAL_ENV
ARG VERSION
ENV VERSION=${VERSION:-dev} \
    LOCAL_ENV=${LOCAL_ENV:-0}
EXPOSE 5000
ENTRYPOINT ["/bin/sh", "docker-entrypoint.sh"]
