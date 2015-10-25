'use strict';
const http = require('http');
const cookie_reader = require('cookie');
const querystring = require('querystring');
const request = require('request');

const NODE_PORT = process.env.NODE_PORT;
const HOST = process.env.NODE_HOST;
const HOST_PORT = process.env.NODE_HOST_PORT;
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

io.on('connection', function (socket) {
  const user = cookie_reader.parse(socket.request.headers.cookie).sessionid
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
})
