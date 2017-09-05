FROM node:8
MAINTAINER thomas@maurin.io
ENV HOME=/app \
    PORT=5001 \
    FORUM_URI=forum:5000 \
    DEBUG=false
COPY . $HOME
WORKDIR $HOME
RUN yarn --ignore-optional --pure-lockfile --production=true
EXPOSE $PORT
CMD node server.js $PORT
