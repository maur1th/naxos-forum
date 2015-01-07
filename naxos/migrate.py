# CoolForum database migration scripts
# Feed it JSON
import os
import re
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

    def double_quote(match_obj):
        return match_obj.group(1) + "\"" + match_obj.group(2) + "\","

    print('Repairing JSON')
    f = open(f)
    lines = f.readlines()
    # Remove comments at the top (illegal in json)
    while lines[0][0] != '[':
        lines.pop(0)
    s = ''.join(lines)
    s = s.replace('\\\'', '\'')  # Esc single quotes inside double is illegal
    s = s.replace('\t', '').replace('\n', '')
    s = s.replace('<br />', '\\n')
    # Add double quotes when missing
    s = re.sub(r'[^\x20-\x7e]', '', s)
    s = re.sub(r'("msg": )([^"]*[^\\]),', double_quote, s)
    # print(re.findall(r'"msg": ([^"]*[^\\]),', s))
    print(repr(s[15479985:15479995]))
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
        m = ForumUser.objects.filter(pk=user['userid']).first()
        if m: m.delete()
        m = ForumUser.objects.filter(
            username=HTMLParser().unescape(user['login'])).first()
        if m: m.delete()
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
    cat = {1:1, 2:2, 3:3, 4:4, 5:6, 6:7, 7:5}  # mapping categories
    threads = json.loads(fix_json(f))
    for i, thread in enumerate(threads):
        m = Thread.objects.filter(pk=thread['idtopic']).first()
        if m: m.delete()
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

import_users(here('..', '..', '..', 'util', 'data', 'new.json'))
# import_threads(here('..', '..', '..', 'util', 'data', 'CF_topics.json'))
# json.loads(fix_json(here('..', '..', '..', 'util', 'data', 'CF_posts.json')))
