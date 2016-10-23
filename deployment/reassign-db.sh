#!/bin/bash
sudo -u postgres sh -c "psql -d naxos -c 'REASSIGN OWNED BY webadmin TO vagrant;'"
