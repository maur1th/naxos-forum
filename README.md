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

The development server is accessible at: <http://localhost:8080>.

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

```bash
docker build --build-arg VERSION="$(git rev-parse HEAD)" --tag maur1th/naxos-forum app/forum
docker tag maur1th/naxos-forum maur1th/naxos-forum:"$(git rev-list --tags --max-count=1)"
docker push maur1th/naxos-forum
docker push maur1th/naxos-forum:"$(git rev-list --tags --max-count=1)"
```

## Deployment

### Application

```bash
# Deploy latest Docker images
$ ansible-playbook -i hosts --vault-password-file=~/.vault_pass playbook.yml
# Deploy specific commit
$ ansible-playbook -i hosts --vault-password-file=~/.vault_pass playbook.yml -e "app_version=<version>"
```

### Static files

```bash
docker-compose run -e LOCAL_ENV=0 -e AWS_STORAGE_BUCKET_NAME=geekattitude -e AWS_ACCESS_KEY_ID=foo -e AWS_SECRET_ACCESS_KEY=bar --entrypoint "python3 manage.py collectstatic --no-input" forum
```
