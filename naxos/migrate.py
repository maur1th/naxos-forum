import os
import json
import django
from html.parser import HTMLParser
from datetime import datetime
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naxos.settings.local")
django.setup()

from naxos.settings.local import here
from user.models import ForumUser
from forum.util import keygen


def import_users(source):
    """Import users from a CoolForum json db extract"""
    f = open(source)
    users = json.loads(f.read())

    for i, user in enumerate(users):
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
        password = keygen()
        u = ForumUser.objects.create(
            pk=user['userid'],
            username=HTMLParser().unescape(user['login']),
            email=HTMLParser().unescape(user['usermail']),
            date_joined=datetime.fromtimestamp(user['registerdate']),
            logo="logo/{:s}".format(user['userlogo']),
            quote=HTMLParser().unescape(str(user['usercitation'])),
            website=HTMLParser().unescape(str(user['usersite'])),
        )
        print("Creating {:d}/{:d}: {:s} with password {:s}".format(
            i, len(users), u.username, password))
        u.set_password(password)
        u.save()
        # send email with password


import_users(here('..', '..', '..', 'util', 'data', 'new.json'))
