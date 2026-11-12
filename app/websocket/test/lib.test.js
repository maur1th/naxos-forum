'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const {hashUser, makeAuthMiddleware, makeNotifier, makeConnectionTracker} = require('../lib');

const URL_ = 'http://forum:5000/user/node_api/';

test('hashUser is a short hex tag that does not contain the session id', () => {
  const tag = hashUser('sess-abc123');
  assert.match(tag, /^[0-9a-f]{8}$/);
  assert.ok(!tag.includes('sess'));
  assert.equal(hashUser('sess-abc123'), tag);
  assert.notEqual(hashUser('other'), tag);
});

const parse = h => Object.fromEntries(h.split(';').map(p => p.trim().split('=')));
const run = headers => {
  const calls = [];
  makeAuthMiddleware(parse)({request: {headers}}, (...a) => calls.push(a));
  return calls;
};

test('auth middleware calls next() once, without error, for a sessionid cookie', () => {
  const calls = run({cookie: 'sessionid=abc'});
  assert.equal(calls.length, 1);
  assert.equal(calls[0].length, 0);
});

test('auth middleware rejects (once) a cookie header without sessionid', () => {
  const calls = run({cookie: 'foo=bar'});
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0].message, 'not authorized');
});

test('auth middleware rejects a missing cookie header', () => {
  const calls = run({});
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0].message, 'not authorized');
});

test('makeNotifier POSTs the session id in the body with the secret header', async () => {
  const calls = [];
  const notify = makeNotifier(URL_, 's3cret', {fetchImpl: (...a) => (calls.push(a), Promise.resolve())});
  await notify('u1', 'connected');
  assert.equal(calls.length, 1);
  const [url, opts] = calls[0];
  assert.equal(url, URL_);
  assert.ok(!url.includes('u1'));
  assert.equal(opts.method, 'POST');
  assert.equal(opts.headers['X-Node-Secret'], 's3cret');
  assert.equal(opts.body, 'sessionid=u1&status=connected');
});

test('makeNotifier swallows fetch failures (fire-and-forget)', async () => {
  const errors = [];
  const notify = makeNotifier(URL_, 's', {
    fetchImpl: () => Promise.reject(new Error('boom')),
    onError: err => errors.push(err.message),
  });
  await assert.doesNotReject(notify('u1', 'connected'));
  assert.deepEqual(errors, ['boom']);
});

test('makeNotifier works end-to-end against a real server with global fetch', async () => {
  const received = [];
  const server = http.createServer((req, res) => {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', () => {
      received.push([req.method, req.url, req.headers['x-node-secret'], body]);
      res.writeHead(200);
      res.end('ok');
    });
  });
  await new Promise(resolve => server.listen(0, resolve));
  try {
    const {port} = server.address();
    const notify = makeNotifier(`http://127.0.0.1:${port}/user/node_api/`, 'k');
    await notify('real-user', 'connected');
    assert.deepEqual(received, [['POST', '/user/node_api/', 'k', 'sessionid=real-user&status=connected']]);
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
});

test('tracker: first connect is the edge, extra tabs are not', () => {
  const t = makeConnectionTracker();
  assert.equal(t.connect('u'), true);   // first tab -> notify connected
  assert.equal(t.connect('u'), false);  // second tab -> no notify
  assert.equal(t.connect('u'), false);  // third tab -> no notify
  assert.equal(t.count('u'), 3);
});

test('tracker: only the last disconnect is the edge', () => {
  const t = makeConnectionTracker();
  t.connect('u'); t.connect('u'); t.connect('u'); // 3 tabs open
  assert.equal(t.disconnect('u'), false); // 2 left
  assert.equal(t.disconnect('u'), false); // 1 left
  assert.equal(t.disconnect('u'), true);  // last tab closed -> notify disconnected
  assert.equal(t.count('u'), 0);
});

test('tracker: disconnect of an unknown user is not an edge', () => {
  const t = makeConnectionTracker();
  assert.equal(t.disconnect('ghost'), false);
  assert.equal(t.count('ghost'), 0);
});

test('tracker: users are tracked independently', () => {
  const t = makeConnectionTracker();
  assert.equal(t.connect('a'), true);
  assert.equal(t.connect('b'), true);
  assert.equal(t.disconnect('a'), true);
  assert.equal(t.count('a'), 0);
  assert.equal(t.count('b'), 1);
});

test('tracker: a user can reconnect after fully disconnecting', () => {
  const t = makeConnectionTracker();
  t.connect('u');
  assert.equal(t.disconnect('u'), true);
  assert.equal(t.connect('u'), true); // fresh session -> edge again
});
