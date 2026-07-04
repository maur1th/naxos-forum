'use strict';
const http = require('http');
const cookie_reader = require('cookie');

const {PORT, DEBUG, FORUM_URI} = process.env;

const app = http.createServer().listen(PORT);
const io = require('socket.io')(app);
const connected_users = {};
const url = `http://${FORUM_URI}/user/node_api`;

// Fire-and-forget notification to django. Swallows errors to match the
// previous `request` behaviour (no callback) and avoid unhandled rejections.
const notifyForum = (user, status) => {
  const params = new URLSearchParams({sessionid: user, status});
  fetch(`${url}?${params}`).catch(err => console.error('node_api notify failed:', err.message));
};

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
    console.log(user + ' connected');
    // Tell django the user has come online
    notifyForum(user, 'connected');
  }
}

const handleDisconnection = (socket, user) => {
  socket.on('disconnect', () => {
    setTimeout(() => {
      if (connected_users[user] === 1) {
        delete connected_users[user];
        console.log(user + ' disconnected');
        // Tell django the user is now offline
        notifyForum(user, 'disconnected');
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
