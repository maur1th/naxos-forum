# Naxos-Forum

## Purpose

Bulletin board project created to replace a [CoolForum](https://github.com/dsoriano/coolforum) solution. (Including DB migration script.) Comes with a light community blog.

Made in Python 3. Backend mostly based on Django, PostgreSQL and memcached. Frontend in BootStrap + JQuery. Node.js + Socket.io for some realtime capabilities. Deploys with Docker & Ansible.

## Getting started

### Prerequisite

Install [Docker](https://www.docker.com/community-edition)

### Starting a development environment

The development environment uses `docker-compose`, more information on the CLI usage [here](https://docs.docker.com/compose/reference/).

```bash
docker-compose up -d          # Start environment
docker-compose logs -f        # Read all components logs
docker-compose logs -f forum  # Read forum component logs
docker-compose exec forum sh  # Execute an interactive shell on the forum container
```

The development server is accessible at: <http://localhost:8081>.

### Stopping a development environment

```bash
docker-compose down              # Stop environment (add -v to delete the volumes)
docker volume ls                 # List volumes
docker volume rm naxos_forum-db  # Delete the db
```

### Fixtures

Initial data (fixtures) is provided and installed automatically by `docker-entrypoint.sh`.

Out of the box, you will be able to log in using those credentials:

- Username: "admin"
- Password: "crimson"

#### Create new fixtures

```sh
python3 manage.py dumpdata --natural-foreign \
   --exclude auth.permission --exclude contenttypes \
   --indent 4 > data.json
```

## Building

### Update dependencies

```bash
pipenv run pip install setuptools==57.5.0
pipenv install
pipenv update
pipenv requirements > requirements.txt
```

### Docker image

Images are built by CI: once the `test` workflow passes on main,
`.github/workflows/images.yml` builds `maur1th/naxos-forum` and
`maur1th/naxos-websocket` for `linux/arm64` (the production host is a Graviton
instance) and pushes them to Docker Hub, tagged with the commit SHA and
`latest`. To build an older commit, run the workflow by hand:
`gh workflow run images.yml -f ref=<sha>`.

## Deployment

### Application

The production host runs Amazon Linux 2 (Python 2.7 and 3.7 only), which
ansible-core 2.17+ can't manage, so the playbook runs from a pinned container
(`deployment/runner/Dockerfile`, ansible-core 2.16). It needs Docker, the SSH
key at `~/.ssh/tmaurin-change` and the vault password at `~/.vault_pass`
(override with `NAXOS_SSH_KEY` and `NAXOS_VAULT_PASS`).

```bash
# Deploy a specific commit (its images must have been pushed by CI)
$ deployment/run-playbook.sh playbook.yml -e "app_version=<sha>"
# Dry run
$ deployment/run-playbook.sh playbook.yml --check -e "app_version=<sha>"
```

With Claude Code, `/deploy [PR number or SHA]` does this end to end.

### Static files

```bash
docker-compose run -e LOCAL_ENV=0 -e AWS_STORAGE_BUCKET_NAME=geekattitude -e AWS_ACCESS_KEY_ID=foo -e AWS_SECRET_ACCESS_KEY=bar --entrypoint "python3 manage.py collectstatic --no-input" forum
```
