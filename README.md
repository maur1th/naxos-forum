# Naxos
Bulletin board project created to replace a [CoolForum](https://github.com/dsoriano/coolforum) solution. (Including DB migration script.) Comes with a light community blog.

Made in Python 3. Backend mostly based on Django, PostgreSQL and memcached. Frontend in BootStrap + JQuery. Node.js + Socket.io for realtime capabilities. Deploys with Ansible.

## Getting started
1. Install both `vagrant` and `ansible`
2. `vagrant up`

Can be done on OSX in just a few steps:
```bash
$ # Install Homebrew
$ /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
$ # Install deps
$ brew cask install virtualbox
$ brew cask install vagrant && vagrant plugin install vagrant-hostsupdater
$ brew install ansible
$ # run
$ vagrant up
```

In case `vagrant up` fails during provisioning, provision again using `vagrant provision`.

By default, a test user is created with username `test` and password `123456`.
