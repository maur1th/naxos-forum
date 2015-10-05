#!/bin/bash
# Ubuntu 14.04 setup script
apt-get install -y git build-essential python3 python3-pip virtualenvwrapper nginx postgresql postgresql-server-dev-9.3 memcached libmemcached-dev python-imaging nginx supervisor libjpeg-dev libtiff5-dev libfreetype6-dev liblcms2-dev libwebp-devgroupadd --system webapps
useradd --system --gid webapps --shell /bin/bash --home /webapps/forum forum
mkdir -p /webapps/forum
chown forum /webapps/forum
su - forum
mkvirtualenv -p /usr/bin/python3 v-env
git clone https://github.com/maur1th/naxos-project.git
pip install -r naxos-project/requirements/production.txt
