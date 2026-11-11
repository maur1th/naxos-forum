# Ansible controller for deploying to the production host.
#
# The host runs Amazon Linux 2, whose only Python with the Docker SDK is
# Python 2.7. ansible-core 2.17+ cannot manage Python 2 (or 3.7) targets, so
# this pins the last line that can: ansible-core 2.16 with community.docker 3.x.
FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-client \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir 'ansible-core>=2.16,<2.17' \
    && ansible-galaxy collection install -p /usr/share/ansible/collections \
        'community.docker:>=3,<4' 'community.general:>=8,<9' 'ansible.posix:>=1,<2'
WORKDIR /deployment
ENTRYPOINT ["ansible-playbook"]
