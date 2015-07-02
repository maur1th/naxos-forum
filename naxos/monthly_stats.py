# monthly_stats.py

import os
import django
from datetime import datetime
from heapq import nlargest
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naxos.settings.dev")
django.setup()

from user.models import ForumUser


startMonth = datetime(2015, 6, 1)
endMonth = datetime(2015, 7, 1)


def get_post_count(model):
    user_post_count = {}
    for user in model.objects.iterator():
        user_post_count[user.username] = user.posts.filter(
            created__gte=startMonth, created__lt=endMonth).count()
    return user_post_count


def top_ten_posters(model):
    post_count = get_post_count(model)
    for user, count in nlargest(
            10, post_count.items(), key=lambda k: k[1]):
        print(user, count)


top_ten_posters(ForumUser)
