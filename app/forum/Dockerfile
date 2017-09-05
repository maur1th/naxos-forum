FROM python:3.6 AS builder
RUN apt-get update && apt-get install -y \
        libjpeg-dev \
        libtiff5-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libwebp-dev \
        libmemcached-dev
RUN apt-get install
COPY requirements* /
ARG LOCAL_ENV
RUN if [ $LOCAL_ENV -eq 1 ]; then \
        pip3 install -r requirements-dev.txt --target /packages; \
    else \
        pip3 install -r requirements-prd.txt --target /packages; \
    fi

FROM python:3.6-slim
MAINTAINER thomas@maurin.io
ENV HOME=/app \
    PYTHONPATH=/packages \
    WORKERS=2
COPY --from=builder /packages /packages
COPY bin/gunicorn /usr/local/bin/gunicorn
COPY . $HOME
WORKDIR $HOME
EXPOSE 5000
ARG LOCAL_ENV
ENV LOCAL_ENV ${LOCAL_ENV:-0}
ENTRYPOINT ["/bin/sh", "docker-entrypoint.sh"]
