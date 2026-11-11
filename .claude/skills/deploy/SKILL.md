---
name: deploy
description: Deploy a new version of naxos-forum to production (geekattitude.org) after a PR is merged to master. Waits for the images workflow to push that commit's Docker images, runs the Ansible playbook pinned to it, then checks the running containers. Use when the user asks to deploy, ship or release, or to put a merged PR live.
argument-hint: "[PR number or commit SHA — defaults to the tip of origin/master]"
disable-model-invocation: true
---

# Deploy naxos-forum

Production is a single arm64 EC2 host, `geekattitude.org` (`deployment/hosts`).
Images are built by CI, not here: after the `test` workflow passes on master,
`.github/workflows/images.yml` builds `maur1th/naxos-forum` and
`maur1th/naxos-websocket` for `linux/arm64` and pushes them to Docker Hub,
tagged with the full commit SHA and `latest`. A deploy runs the Ansible
playbook pinned to that SHA and then checks what the server runs.

This changes the live forum, so **ask the user to confirm before step 4**, and
stop at the first step that fails. Never deploy a commit that is not on
`origin/master`.

SSH to the host uses the key `~/.ssh/tmaurin-change` as `ec2-user`. Below,
`SSH` means:

```bash
ssh -i ~/.ssh/tmaurin-change -o IdentitiesOnly=yes -o BatchMode=yes ec2-user@geekattitude.org
```

## 1. Find the commit

1. `git fetch origin master`.
2. Find the commit to deploy:
   - No argument: `origin/master`.
   - PR number: `gh pr view <n> --json state,mergeCommit,title`. If `state` is
     not `MERGED`, stop and tell the user. Use `mergeCommit.oid`.
   - SHA: use it, after checking `git merge-base --is-ancestor <sha> origin/master`.
3. Set `SHA` to the full 40-character hash (`git rev-parse <ref>`).

## 2. Check the tools and what is live

Check all of these, and report every missing one at once:

- Docker is running (`docker info`). Ansible runs from a pinned container
  (`deployment/run-playbook.sh`, built from `deployment/runner/Dockerfile`),
  not the system `ansible-playbook`: the host's Amazon Linux 2 only has
  Python 2.7 and 3.7, which ansible-core 2.17+ can't manage.
- `~/.vault_pass` and `~/.ssh/tmaurin-change` exist with mode `600`. Never
  print or read either file.
- `SSH true` succeeds.

Then see what is live: `SSH 'sudo docker exec forum printenv VERSION'`. (The
site's `/version` page is behind the login, so check the container instead.)
If it already prints `$SHA`, tell the user there is nothing to deploy and
stop. Otherwise show what goes out with `git log --oneline <live>..$SHA`.

## 3. Wait for the images

1. Find the images run for the commit:
   `gh run list --workflow images.yml --commit "$SHA" --json databaseId,status,conclusion,url`.
   - Still running: `gh run watch <id> --exit-status`.
   - Failed: show the run URL and the failing step (`gh run view <id> --log-failed`), and stop.
   - No run at all: check the `test` run for the commit
     (`gh run list --workflow test.yml --commit "$SHA"`). If tests failed,
     stop: images are only built for commits that pass. If tests passed but
     there is no images run (for example a commit from before the workflow
     existed), offer to start one with
     `gh workflow run images.yml -f ref="$SHA"`, then watch it.
2. Confirm both tags exist on Docker Hub as arm64:
   `docker buildx imagetools inspect maur1th/naxos-forum:"$SHA"` and the same
   for `maur1th/naxos-websocket`. Each must list `linux/arm64`.

## 4. Run the playbook

Ask the user to confirm: "Deploy `<short sha>` (`<commit subject>`) to
geekattitude.org?" Go on only on a yes.

Pin the version so the host pulls exactly the images CI pushed. The wrapper
mounts `deployment/`, the SSH key and the vault password into the container
read-only, and uses `deployment/ansible.cfg`:

```bash
deployment/run-playbook.sh playbook.yml -e "app_version=$SHA"
```

If anything about the run looks risky, do a dry run first by adding `--check`:
it reports what would change without touching the host.

This runs the whole playbook (Docker, Postgres, memcached, forum, certbot,
nginx), which is how the project has always deployed. It stops and recreates
every container, Postgres and nginx included, so the site is down briefly.
The forum container runs migrations on start (`docker-entrypoint.sh`).

If the playbook fails, show the failing task and its error, and stop. Don't
rerun it with changes to roles or inventory unless the user asks.

## 5. Verify

1. `SSH 'sudo docker ps --format "{{.Names}} {{.Image}} {{.Status}}"'`:
   `forum` and `websocket` should run the `:$SHA` images and be `Up`, not
   restarting.
2. `SSH 'sudo docker exec forum printenv VERSION'` prints `$SHA`.
3. `curl -sS -o /dev/null -w '%{http_code} %{redirect_url}' https://geekattitude.org/`
   gives `200`, or `302` to `/user/login/`. A `502` means nginx can't reach
   the forum: give it a minute, then check again.
4. If any check fails, show `SSH 'sudo docker logs --tail 100 forum'`.

## Rolling back

Rerun step 4 with the SHA that was live in step 2 as `app_version`; its images
are still on Docker Hub. This does not reverse database migrations, so check
`git diff <old>..$SHA --stat -- '*/migrations/*'` first and tell the user if
the release added any.

## Report

End with the deployed short SHA and commit subject, the PRs it included, the
verification results, and anything that went wrong or was skipped.
