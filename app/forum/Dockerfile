FROM python:3.10-alpine AS builder
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

FROM python:3.10-alpine
LABEL maintainer="https://github.com/maur1th"
ENV HOME=/app \
    PYTHONDONTWRITEBYTECODE=1 \
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
RUN adduser -D -H -u 10001 app

ARG LOCAL_ENV
ARG VERSION
ENV VERSION=${VERSION:-dev} \
    LOCAL_ENV=${LOCAL_ENV:-0}
EXPOSE 5000
USER app
ENTRYPOINT ["/bin/sh", "docker-entrypoint.sh"]
