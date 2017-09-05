FROM node:8 AS builder
ENV HOME=/app
COPY . $HOME
WORKDIR $HOME
RUN yarn --ignore-optional --pure-lockfile --production=true

FROM node:8-slim
ENV HOME=/app \
    PORT=5001 \
    FORUM_URI=forum:5000 \
    DEBUG=false
COPY --from=builder $HOME $HOME
WORKDIR $HOME
EXPOSE $PORT
CMD node server.js $PORT
