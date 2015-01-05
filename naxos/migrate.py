import os
import json
import django
from html.parser import HTMLParser
from datetime import datetime
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naxos.settings.local")
django.setup()

from user.models import ForumUser


def import_users(source):
    """Import users from a CoolForum json db extract"""
    f = open(source)
    users = json.loads(f.read())

    for user in users:
        user['login'] = user['login'].replace(' ', '_')[:30]
        try:
            m = ForumUser.objects.get(pk=user['userid'])
            print("Deleting {:s}".format(m.username))
            m.delete()
        except:
            pass
        try:
            m = ForumUser.objects.get(
                username=HTMLParser().unescape(user['login']))
            print("Deleting {:s}".format(m.username))
            m.delete()
        except:
            pass
        u = ForumUser.objects.create(
            pk=user['userid'],
            username=HTMLParser().unescape(user['login']),
            email=HTMLParser().unescape(user['usermail']),
            date_joined=datetime.fromtimestamp(user['registerdate']),
            logo="logo/{:s}".format(user['userlogo']),
            quote=HTMLParser().unescape(str(user['usercitation'])),
            website=HTMLParser().unescape(str(user['usersite'])),
        )
        u.set_password('crimson')  # gen random password
        u.save()
        # send email with password


import_users('new.json')
