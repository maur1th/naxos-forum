import os
import re

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naxos.settings.prod")
django.setup()

from forum.models import Post


print(Post.objects.count())
i = 0
for p in Post.objects.iterator():
    i += 1
    print(i, end='\r')
    m = re.search('beta.geekattitude.org', p.content_plain)
    if not m: continue
    print('match!')
    p.content_plain = p.content_plain.replace(
        'beta.geekattitude.org', 'geekattitude.org')
    p.save()

