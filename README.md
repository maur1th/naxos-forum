Naxos
=====
Purpose
-------
Bulletin board project created to replace a [CoolForum](https://github.com/dsoriano/coolforum) solution. (Including DB migration script.) Comes with a light community blog.

Made in Python 3. Backend mostly based on Django, PostgreSQL and memcached. Frontend in BootStrap + JQuery. Node.js + Socket.io for some realtime capabilities. Deploys with Docker & Ansible.

Getting started
---------------
### Prerequisite
Install [Docker](https://www.docker.com/community-edition)

### Starting a development environment
The development environment uses `docker-compose`, more information on the CLI usage [here](https://docs.docker.com/compose/reference/).
```bash
$ docker-compose up -d          # Start environment
$ docker-compose logs -f        # Read component logs
$ docker-compose exec forum sh  # Execute an interactive shell on the container
$ docker-compose stop           # Stop environment
```
The development server is accessible at: http://localhost:8080.

#### Note
First startup will likely fail because of the db init time. If http://localhost:8080 is unreachable, restart the `forum` component: `$ docker-compose restart forum`.

### Admin website
Admin website is accessible from http://localhost:8080, credentials are: "admin" / "crimson".

### Fixtures
Initial data (fixtures) is provided and installed automatically by `docker-entrypoint.sh`.

Out of the box, you will be able to log in using those credentials:
- Username: "User1"
- Password: "crimson"

Deployment
---------------
```bash
$ ansible-playbook -i hosts-prod --vault-password-file=~/.vault_pass site.yml -e "version=<version>"
```
