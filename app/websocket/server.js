'use strict';
const http = require('http');
const cookie_reader = require('cookie');
const {makeNotifier, makeConnectionTracker} = require('./lib');

const {PORT, DEBUG, FORUM_URI} = process.env;

const app = http.createServer().listen(PORT);
const io = require('socket.io')(app);
const notifyForum = makeNotifier(`http://${FORUM_URI}/user/node_api`);
const tracker = makeConnectionTracker();

io.use((socket, next) => {
  const handshakeData = socket.request;
  if(handshakeData.headers.cookie){
    next();
  }
  next(new Error('not authorized'));
});

const handleConnection = (socket, user) => {
  if (tracker.connect(user)) {
    console.log(user + ' connected');
    // Tell django the user has come online
    notifyForum(user, 'connected');
  }
}

const handleDisconnection = (socket, user) => {
  socket.on('disconnect', () => {
    setTimeout(() => {
      if (tracker.disconnect(user)) {
        console.log(user + ' disconnected');
        // Tell django the user is now offline
        notifyForum(user, 'disconnected');
      }
    }, 5000);
  });
}

io.on('connection', socket => {
  const user = cookie_reader.parse(socket.request.headers.cookie).sessionid;
  handleConnection(socket, user);
  handleDisconnection(socket, user);
});
