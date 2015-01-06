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
from forum.models import Category, Thread
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


def convert_username(name):
    """Convert the username to a naxos-db compliant format"""
    return HTMLParser().unescape(name.replace(' ', '_'))[:30]


def import_users(f):
    """Import users from a CoolForum json db extract"""
    f = open(f)
    users = json.loads(f.read())

    for i, user in enumerate(users):
        user['login'] = convert_username(user['login'])
        try:
            m = ForumUser.objects.get(pk=user['userid'])
            m.delete()
        except:
            pass
        try:
            m = ForumUser.objects.get(
                username=HTMLParser().unescape(user['login']))
            m.delete()
        except:
            pass
        password = keygen()
        u = ForumUser.objects.create(
            pk=int(user['userid']),
            username=user['login'],
            email=HTMLParser().unescape(user['usermail']),
            date_joined=datetime.fromtimestamp(user['registerdate']),
            logo="logo/{:s}".format(user['userlogo']),
            quote=HTMLParser().unescape(str(user['usercitation'])),
            website=HTMLParser().unescape(str(user['usersite'])),
        )
        print("Creating {:d}/{:d}: {:s} with password {:s}".format(
            i+1, len(users), u.username, password))
        u.set_password(password)
        u.save()
        # TODO: send email with new password


def import_threads(f):
    cat = {1:1, 2:2, 3:3, 4:4, 5:6, 6:7, 7:5}
    threads = json.loads(fix_json(f))
    for i, thread in enumerate(threads):
        try:
            m = Thread.objects.get(pk=thread['idtopic'])
            m.delete()
        except:
            pass
        t = Thread.objects.create(
            pk=int(thread['idtopic']),
            category=Category.objects.get(pk=cat[thread['idforum']]),
            title=HTMLParser().unescape(str(thread['sujet']))[:80],
            author=ForumUser.objects.get(pk=thread['idmembre']),
            viewCount=int(thread['nbvues']),
            # modified=datetime.fromtimestamp(thread['date']),
        )
        # print("Creating {:d}/{:d}".format(i+1, len(threads)))


# TODO: override thread.modified with latest topic datetime

# import_users(here('..', '..', '..', 'util', 'data', 'new.json'))
# import_threads(here('..', '..', '..', 'util', 'data', 'CF_topics.json'))
json.loads(fix_json(here('..', '..', '..', 'util', 'data', 'CF_topics.json')))
