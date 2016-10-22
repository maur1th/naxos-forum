#!/bin/bash
ansible-playbook -i production --vault-password-file ~/.vault_pass site.yml
