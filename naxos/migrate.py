# CoolForum database migration scripts
# Feed it JSON
import os
import re
import json
import django
from html.parser import HTMLParser
from datetime import datetime
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "naxos.settings.dev")
django.setup()

from naxos.settings.base import here
from user.models import ForumUser
from forum.models import Category, Thread, Post
from forum.util import keygen


# PLEASE NOTE THAT CATEGORIES HAVE TO BE CREATED FIRST AND UPDATE 'cat_map'
# ACCORDINGLY


def fix_json(f):
    """Fixes phpmyadmin json exports"""

    def double_quote(match_obj):
        quote = match_obj.group(2)
        return match_obj.group(1) + "\"" + quote + "\","

    print('Repairing JSON')
    f = open(f)
    lines = f.readlines()
    # Remove comments at the top (illegal in json)
    while lines[0][0] != '[':
        lines.pop(0)
    s = ''.join(lines)
    s = s.replace('<br />', '\\n')  # User proper new line character
    s = s.replace('\\\'', '\'')  # Remove illegal escapes for squotes
    s = re.sub(r'[^\x20-\x7e]', '', s)  # remove hex characters
    # add double quotes where missing
    s = re.sub(r'("msg": )([^"]*),', double_quote, s)
    s = re.sub(r'("usercitation": )([^"]*),', double_quote, s)
    # let's roll
    print("All right, good to go.")
    return s


def convert_username(name):
    """Convert the username to a naxos-db compliant format"""
    return HTMLParser().unescape(name.replace(' ', '_'))[:30]


def import_users(f):
    """Import users from a CoolForum json db extract"""
    users = json.loads(fix_json(f))
    new_users = {}

    for i, user in enumerate(users):
        user['login'] = convert_username(user['login'])
        m = ForumUser.objects.filter(pk=user['userid']).first()
        if m: m.delete()  # delete the user if it already exists
        password = keygen()  # gen password
        new_users[user['login']] = password
        u = ForumUser.objects.create(
            pk=int(user['userid']),
            username=user['login'],
            email=HTMLParser().unescape(user['usermail']),
            date_joined=datetime.fromtimestamp(user['registerdate']),
            logo="logo/{:s}".format(user['userlogo']),
            quote=HTMLParser().unescape(str(user['usercitation'])),
            website=HTMLParser().unescape(str(user['usersite'])),
        )
        print("Creating users... {:d}/{:d}: {:s}{:s}".format(
            i+1, len(users), u.username, " "*(30-len(u.username))), end="\r")
        u.set_password(password)
        u.save()
    print()
    f = open('new_users.json', 'w')
    json.dump(new_users, f)
    f.close()
    # TODO: send email with new password


def import_threads(f):
    cat_map = {1:1, 2:2, 3:3, 4:4, 5:6, 6:7, 7:5}  # mapping categories
    threads = json.loads(fix_json(f))
    for i, thread in enumerate(threads):
        m = Thread.objects.filter(pk=thread['idtopic']).first()
        if m: m.delete()  # delete the thread if it already exists
        t = Thread.objects.create(
            pk=int(thread['idtopic']),
            category=Category.objects.get(pk=cat_map[thread['idforum']]),
            title=HTMLParser().unescape(str(thread['sujet']))[:80],
            author=ForumUser.objects.get(pk=thread['idmembre']),
            icon=str(thread['icone'])+'.gif',
            viewCount=int(thread['nbvues']),
        )
        print("Creating threads... {:d}/{:d}".format(
            i+1, len(threads)), end="\r")
    print()

def import_posts(f):
    posts = json.loads(fix_json(f))
    users = {}
    print('Loading threads...')
    existing_threads = {}
    for thread in Thread.objects.all():
        existing_threads[thread.pk] = thread.category_id
    print('done')
    print('Loading posts...')
    existing_posts = set()
    for post in Post.objects.all():
        existing_posts.add(post.pk)
    print('done')
    post_counter = {}  # stores the number of posts per cat
    for category in Category.objects.all():  # initializing dict values
        post_counter[category.pk] = 0
    for i, post in enumerate(posts):
        print("Creating {:d}/{:d}".format(i+1, len(posts)), end="\r")
        # skip if thread does not exist
        if post['parent'] not in existing_threads: continue
        # increment category post counter
        post_counter[existing_threads[post['parent']]] += 1
        # skip if post already exists
        if post['idpost'] in existing_posts: continue
        p = Post.objects.create(
            pk=int(post['idpost']),
            thread_id=int(post['parent']),
            author_id=int(post['idmembre']),
            created=datetime.fromtimestamp(post['date']),
            content_plain=str(post['msg']),
        )
    threads = Thread.objects.all()
    for i, thread in enumerate(threads):
        print('Updating thread modified datetime: {:d}/{:d}'.format(
            i+1, len(threads)), end="\r")
        thread.modified = thread.posts.latest.modified
        thread.save()
    for key, value in post_counter:
        print('Updating post counter')
        c = Category.objects.get(pk=key)
        c.postCount = value
        c.save()


# TODO: add count posts
# TODO: override thread.modified with last topic datetime

# import_users(here('..', '..', '..', 'util', 'data', 'CF_user.json'))
# import_threads(here('..', '..', '..', 'util', 'data', 'CF_topics.json'))
import_posts(here('..', '..', '..', 'util', 'data', 'CF_posts.json'))
