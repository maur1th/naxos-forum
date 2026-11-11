#!/bin/sh
# Run ansible-playbook from the pinned controller image (see runner/Dockerfile).
# Usage: deployment/run-playbook.sh [ansible-playbook args...]
# e.g.   deployment/run-playbook.sh playbook.yml -e app_version=<sha>
set -eu
here="$(cd "$(dirname "$0")" && pwd)"
key="${NAXOS_SSH_KEY:-$HOME/.ssh/tmaurin-change}"
vault="${NAXOS_VAULT_PASS:-$HOME/.vault_pass}"

docker build --quiet --tag naxos-ansible "$here/runner" >/dev/null
exec docker run --rm ${NAXOS_TTY:+-it} \
  -v "$here:/deployment:ro" \
  -v "$key:/secrets/ssh_key:ro" \
  -v "$vault:/secrets/vault_pass:ro" \
  -e ANSIBLE_PRIVATE_KEY_FILE=/secrets/ssh_key \
  -e ANSIBLE_VAULT_PASSWORD_FILE=/secrets/vault_pass \
  -e ANSIBLE_CONFIG=/deployment/ansible.cfg \
  naxos-ansible -i hosts "$@"
