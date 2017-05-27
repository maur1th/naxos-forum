'use strict';
const http = require('http');
const cookie_reader = require('cookie');
const request = require('request');
const winston = require('winston');

winston.level = 'info';
const {PORT, DEBUG, FORUM_URI} = process.env;

const app = http.createServer().listen(PORT);
const io = require('socket.io')(app);
const connected_users = {};
const url = `http://${FORUM_URI}/user/node_api`;

io.use((socket, next) => {
  const handshakeData = socket.request;
  if(handshakeData.headers.cookie){
    next();
  }
  next(new Error('not authorized'));
});

const handleConnection = (socket, user) => {
  if (user in connected_users) {
    connected_users[user] += 1;
  } else {
    connected_users[user] = 1;
    winston.info(user + ' connected');
    // Tell django the user has come online
    request({url, qs: {sessionid: user, status: 'connected'}});
  }
}

const handleDisconnection = (socket, user) => {
  socket.on('disconnect', () => {
    setTimeout(() => {
      if (connected_users[user] === 1) {
        delete connected_users[user];
        winston.info(user + ' disconnected');
        // Tell django the user is now offline
        request({url, qs: {sessionid: user, status: 'disconnected'}});
      } else {
        connected_users[user] -= 1;
      }
    }, 5000);
  });
}

io.on('connection', socket => {
  const user = cookie_reader.parse(socket.request.headers.cookie).sessionid;
  handleConnection(socket, user);
  handleDisconnection(socket, user);
});
