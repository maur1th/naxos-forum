FROM alpine:3.20

LABEL maintainer="thomas@maurin.io"
ENV HOME=/app \
    PORT=5001 \
    FORUM_URI=forum:5000 \
    DEBUG=false

RUN set -ex \
        && apk add --no-cache \
            nodejs \
            yarn \
        && adduser -D -H -u 10001 node

COPY . $HOME
WORKDIR $HOME

RUN yarn --ignore-optional --pure-lockfile --production=true

EXPOSE $PORT
USER node
CMD ["node", "server.js"]
