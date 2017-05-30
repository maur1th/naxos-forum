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

COPY requirements.txt /
RUN set -ex \
        && apk add --no-cache --virtual .build-deps \
                build-base \
                postgresql-dev \
                libmemcached-dev \
                libjpeg-turbo-dev \
                libwebp-dev \
                zlib-dev \
                cyrus-sasl-dev \
        && pip3 install --no-cache-dir -r requirements.txt \
        && apk del .build-deps

COPY . $HOME
WORKDIR $HOME

EXPOSE 5000
ENTRYPOINT ["/bin/sh", "docker-entrypoint.sh"]
