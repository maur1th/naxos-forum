#!/bin/sh
# Create (or reset) the throwaway login used by the browser tests, in the
# dev database of the running forum container (the one publishing port 8081,
# so it works from any git worktree). Credentials: e2e / e2e-password.
set -e
c="${FORUM_CONTAINER:-$(docker ps --filter publish=8081 --format '{{.Names}}' | head -1)}"
[ -n "$c" ] || { echo "no forum container on :8081 - run 'docker compose up -d forum'" >&2; exit 1; }
docker exec -i "$c" python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
u, _ = U.objects.get_or_create(username='e2e', defaults={'email': 'e2e@example.org'})
u.set_password('e2e-password'); u.is_active = True; u.save()
print('seeded user e2e')
"
