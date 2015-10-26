'use strict';
const http = require('http');
const cookie_reader = require('cookie');
const request = require('request');

const NODE_PORT = process.env.NODE_PORT;
const HOST = process.env.NODE_HOST;
const DEBUG = false;

const app = http.createServer().listen(NODE_PORT);
const io = require('socket.io')(app);
const connected_users = {};

io.use(function (socket, next) {
  const handshakeData = socket.request;
  if(handshakeData.headers.cookie){
    next();
  }
  next(new Error('not authorized'));
});

function handleConnection(socket, user) {
  if (user in connected_users) {
    connected_users[user] += 1;
  } else {
    connected_users[user] = 1;
    if (DEBUG) console.log(user + ' connected');
    // Tell django the user has come online
    request({
      url: HOST + '/user/node_api',
      qs: {sessionid: user, status: 'connected'}
    });
  }
}

function handleDisconnection(socket, user) {
  socket.on('disconnect', function () {
    setTimeout(function () {
      if (connected_users[user] === 1) {
        delete connected_users[user];
        if (DEBUG) console.log(user + ' disconnected');
        // Tell django the user is now offline
        request({
          url: HOST + '/user/node_api',
          qs: {sessionid: user, status: 'disconnected'}
        });
      } else {
        connected_users[user] -= 1;
      }
    }, 5000);
  });
}

io.on('connection', function (socket) {
  const user = cookie_reader.parse(socket.request.headers.cookie).sessionid;
  handleConnection(socket, user);
  handleDisconnection(socket, user);
});
