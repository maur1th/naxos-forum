#!/bin/bash
if [[ "$1" = "full" ]]; then
  ansible-playbook -i prod --vault-password-file ~/.vault_pass site.yml
else
  ansible-playbook -i prod --vault-password-file ~/.vault_pass --skip-tags full-run site.yml
fi
