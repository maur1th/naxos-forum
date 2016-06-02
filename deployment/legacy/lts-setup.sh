#!/bin/bash
# Ubuntu 14.04 setup script
sudo locale-gen en_US.UTF-8
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get install -y git build-essential python3 python3-pip virtualenvwrapper nginx postgresql postgresql-server-dev-9.3 memcached libmemcached-dev python-imaging nginx supervisor libjpeg-dev libtiff5-dev libfreetype6-dev liblcms2-dev libwebp-dev
sudo groupadd --system web
sudo useradd --system --gid web --shell /bin/bash --home /var/www/forum forum
sudo mkdir -p /var/www/forum
sudo chown forum /var/www/forum
sudo chgrp web /var/www/forum
su - forum
mkvirtualenv -p /usr/bin/python3 v-env
git clone https://github.com/maur1th/naxos-project.git
pip install -r naxos-project/requirements/production.txt
