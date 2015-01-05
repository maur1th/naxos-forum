# CoolForum database migration scripts
# Feed it JSON
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


def fix_json(f):
    """Fixes phpmyadmin json exports"""
    print('Repairing JSON')
    f = open(f)
    lines = f.readlines()
    # Remove comments at the top (illegal in json)
    while lines[0][0] != '[':
        lines.pop(0)
    s = ''.join(lines)
    s = s.replace('\\\'', '\'')  # Esc single quotes inside double is illegal
    s = s.replace('\t', '')
    return s


def import_users(f):
    """Import users from a CoolForum json db extract"""
    f = open(f)
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
        # TODO: send email with new password


def import_threads(f):
    f = open(f)
    threads = json.loads(f.read())


# import_users(here('..', '..', '..', 'util', 'data', 'new.json'))
json.loads(fix_json(here('..', '..', '..', 'util', 'data', 'CF_topics.json')))
