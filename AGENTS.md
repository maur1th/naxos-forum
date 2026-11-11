# Agent notes

## GitHub issues

- Open GitHub issues from `.github/ISSUE_TEMPLATE/issue.md`: a `[Critical]`,
  `[High]`, `[Medium]` or `[Low]` title prefix, the `bug` label, and the
  template's sections (Problem, Why it matters, Proof, Proposed fix, Acceptance
  criteria, Recommended model). Also add the matching `model: haiku`,
  `model: sonnet` or `model: opus` label for the model named in the Recommended
  model section. Never put real user data in an issue.

## Running and testing

Python and Django are not installed on the host. Use docker compose for
everything (the `db` service starts automatically; wait a few seconds on the
first run):

```
docker compose build forum
docker compose run --rm --entrypoint python forum manage.py test forum.test_views
docker compose run --rm --no-deps -e LOCAL_ENV=0 -e DEBUG=0 \
  -e AWS_STORAGE_BUCKET_NAME=x -e HOSTNAME=example.org \
  --entrypoint python forum manage.py check --deploy --fail-level WARNING
```

## Frontend dev (Playwright screenshots)

`devtools/` is a small Playwright helper (not a test suite) for looking at the
dev forum in a browser. It uses the Chromium already in
`~/.cache/ms-playwright` and targets `http://localhost:8081`
(`docker compose up -d forum`; override with `FORUM_URL`).

```
cd devtools && npm install
./seed.sh                                   # creates login e2e / e2e-password
node screenshot.mjs /user/login/ out.png [--mobile] [--login]
```

The `/socket.io/socket.io.js` console error is expected: the websocket
service is not part of the dev compose stack.
