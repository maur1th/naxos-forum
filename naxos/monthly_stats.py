# monthly_stats.py

import os
import django
from datetime import datetime
from heapq import nlargest
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naxos.settings.dev")
django.setup()

from user.models import ForumUser
from forum.models import Thread


startMonth = datetime(2015, 6, 1)
endMonth = datetime(2015, 7, 1)


def get_post_count(model_objects):
    post_count = {}
    for obj in model_objects.iterator():
        post_count[obj] = obj.posts.filter(
            created__gte=startMonth, created__lt=endMonth).count()
    return post_count


def top_ten(model_objects):
    post_count = get_post_count(model_objects)
    for i, (obj, count) in enumerate(nlargest(
            10, post_count.items(), key=lambda k: k[1])):
        print(i+1, obj, count)


print("Top 10 des membres ayant le plus posté :")
top_ten(ForumUser.objects)
print()
print("Top 10 des sujets les plus commentés")
top_ten(Thread.objects.filter(modified__gte=startMonth))