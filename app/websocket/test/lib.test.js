'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const {buildNotifyUrl, makeNotifier, makeConnectionTracker} = require('../lib');

const BASE = 'http://forum:5000/user/node_api';

test('buildNotifyUrl builds the expected query string', () => {
  assert.equal(
    buildNotifyUrl(BASE, 'sess-abc123', 'connected'),
    'http://forum:5000/user/node_api?sessionid=sess-abc123&status=connected'
  );
});

test('buildNotifyUrl url-encodes special characters in the session id', () => {
  assert.equal(
    buildNotifyUrl(BASE, 'sess xyz&weird=1', 'disconnected'),
    'http://forum:5000/user/node_api?sessionid=sess+xyz%26weird%3D1&status=disconnected'
  );
});

test('makeNotifier calls fetch with the built url', async () => {
  const calls = [];
  const notify = makeNotifier(BASE, {fetchImpl: url => (calls.push(url), Promise.resolve())});
  await notify('u1', 'connected');
  assert.deepEqual(calls, [`${BASE}?sessionid=u1&status=connected`]);
});

test('makeNotifier swallows fetch failures (fire-and-forget)', async () => {
  const errors = [];
  const notify = makeNotifier(BASE, {
    fetchImpl: () => Promise.reject(new Error('boom')),
    onError: err => errors.push(err.message),
  });
  // Must not reject even though the underlying fetch rejected.
  await assert.doesNotReject(notify('u1', 'connected'));
  assert.deepEqual(errors, ['boom']);
});

test('makeNotifier works end-to-end against a real server with global fetch', async () => {
  const received = [];
  const server = http.createServer((req, res) => {
    received.push(req.url);
    res.writeHead(200);
    res.end('ok');
  });
  await new Promise(resolve => server.listen(0, resolve));
  try {
    const {port} = server.address();
    const notify = makeNotifier(`http://127.0.0.1:${port}/user/node_api`);
    await notify('real-user', 'connected');
    assert.deepEqual(received, ['/user/node_api?sessionid=real-user&status=connected']);
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
