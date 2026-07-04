'use strict';

// Build the node_api notification URL for a user status change.
const buildNotifyUrl = (baseUrl, user, status) =>
  `${baseUrl}?${new URLSearchParams({sessionid: user, status})}`;

// Create a fire-and-forget notifier for the django node_api endpoint.
// `fetchImpl` and `onError` are injectable so the notifier can be unit tested
// without a real network. Errors are swallowed (logged) to avoid unhandled
// rejections, matching the previous `request` (no callback) behaviour.
const makeNotifier = (baseUrl, {
  fetchImpl = fetch,
  onError = err => console.error('node_api notify failed:', err.message),
} = {}) => (user, status) =>
  fetchImpl(buildNotifyUrl(baseUrl, user, status)).catch(onError);

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

module.exports = {buildNotifyUrl, makeNotifier, makeConnectionTracker};
