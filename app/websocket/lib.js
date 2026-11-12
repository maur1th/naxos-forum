'use strict';

const crypto = require('crypto');

// Short, non-reversible tag for logging a session without exposing the
// session ID itself (which is a long-lived login credential).
const hashUser = user =>
  crypto.createHash('sha256').update(String(user)).digest('hex').slice(0, 8);

// socket.io middleware factory: accept only handshakes carrying a cookie
// header with a non-empty `sessionid`. `parseCookie` is injected (the
// `cookie` package's `parse`).
const makeAuthMiddleware = parseCookie => (socket, next) => {
  const header = socket.request.headers.cookie;
  const sessionid = header ? parseCookie(header).sessionid : undefined;
  if (!sessionid) {
    return next(new Error('not authorized'));
  }
  return next();
};

// Create a fire-and-forget notifier for the django node_api endpoint. The
// session ID travels in a POST body (never in the URL) and the request is
// authenticated with a shared secret header.
// `fetchImpl` and `onError` are injectable so the notifier can be unit tested
// without a real network. Errors are swallowed (logged) to avoid unhandled
// rejections.
const makeNotifier = (url, secret, {
  fetchImpl = fetch,
  onError = err => console.error('node_api notify failed:', err.message),
} = {}) => (user, status) =>
  fetchImpl(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'X-Node-Secret': secret || '',
    },
    body: new URLSearchParams({sessionid: user, status}).toString(),
  }).catch(onError);

// Reference-count a user's open sockets (e.g. multiple browser tabs) so django
// is told "connected" only on the first socket and "disconnected" only on the
// last. `connect` returns true on the first connection for a user; `disconnect`
// returns true when the last connection for a user closes.
const makeConnectionTracker = () => {
  const counts = {};
  return {
    connect(user) {
      if (user in counts) {
        counts[user] += 1;
        return false;
      }
      counts[user] = 1;
      return true;
    },
    disconnect(user) {
      const n = counts[user] || 0;
      if (n <= 1) {
        delete counts[user];
        return n === 1;
      }
      counts[user] = n - 1;
      return false;
    },
    count(user) {
      return counts[user] || 0;
    },
  };
};

module.exports = {hashUser, makeAuthMiddleware, makeNotifier, makeConnectionTracker};
