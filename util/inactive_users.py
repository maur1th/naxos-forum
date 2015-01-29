import os
from datetime import datetime

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naxos.settings.dev")
django.setup()

from user.models import ForumUser


TEN_YEARS_FROM_NOW = datetime(2005, 1, 1)
FIVE_YEARS_FROM_NOW = datetime(2010, 1, 1)

zero_post = []
inactive_for_ten_yrs = {}
inactive_for_five_yrs = {}
for u in ForumUser.objects.iterator():
    if not u.posts.exists():
        zero_post.append(u.username)
        continue
    latest_post_date = u.posts.latest().created
    if TEN_YEARS_FROM_NOW > latest_post_date:
        inactive_for_ten_yrs[u.username] = latest_post_date
        continue
    elif FIVE_YEARS_FROM_NOW > latest_post_date:
        inactive_for_five_yrs[u.username] = latest_post_date
        continue

print('Have never posted:')
for user in zero_post:
    print(user)
print('Have been inactive since at least 2005-01-01:')
for user, latest_post_date in inactive_for_ten_yrs.items():
    print(user, "latest post on:", latest_post_date)
print('Have been inactive since at least 2010-01-01:')
for user, latest_post_date in inactive_for_five_yrs.items():
    print(user, "latest post on:", latest_post_date)
