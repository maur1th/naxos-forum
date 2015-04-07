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

from django.db import connection
from django.utils.html import strip_tags

from naxos.settings.base import here
from user.models import ForumUser
from forum.models import Category, Thread, Post
from forum.util import keygen


CUT_OFF_DATE = datetime(2010, 1, 1)

# CATEGORIES HAVE TO BE CREATED FIRST AND UPDATE 'cat_map' ACCORDINGLY


def fix_json(f):
    """Fixes phpmyadmin json exports"""

    def double_quote(match_obj):
        quote = match_obj.group(2)
        return match_obj.group(1) + '"' + quote + '",'

    def clean_invalid_char(match_obj):
        return ': ' + json.dumps(match_obj.group(1)) +','

    filename = os.path.basename(f)
    print('Repairing {}...'.format(filename), end="\r")
    with open(f) as f:
        lines = f.readlines()
    # Remove comments at the top (illegal in json)
    while lines[0][0] != '[':
        lines.pop(0)
    s = ''.join(lines)
    # Remove illegal escapes for squotes
    s = s.replace('\\\'', '\'')
    # add double quotes where missing
    s = re.sub(r'("msg": )([^"]*),', double_quote, s)
    s = re.sub(r'("usercitation": )([^"]*),', double_quote, s)
    # clean invalid characters in JSON
    s = s.split("}, {")
    new = []
    for item in s:
        new.append(re.sub(r': "([\s|\S]*?)",', clean_invalid_char, item))
    s = "}, {".join(new)
    # Good to go
    print("Repairing {}... done".format(filename))
    return s


def import_users(f):

    def convert_username(name):
        """Convert the username to a naxos-db compliant format"""
        return HTMLParser().unescape(name.replace(' ', '_'))[:30]

    s = fix_json(f)
    users = json.loads(s)
    n = len(users)
    new_users = {}
    for i, user in enumerate(users):
        print("Creating users... {}/{}".format(
            i+1, n), end="\r")
        user['login'] = convert_username(user['login'])
        m = ForumUser.objects.filter(pk=user['userid']).first()
        if m: continue
        ### TEMPORARY FIX WHILE HOST BLOCKS SMTP ###
        # password = keygen()  # generate password
        password = HTMLParser().unescape(user['usermail'])
        ### END ###
        new_users[user['login']] = password
        u = ForumUser.objects.create(
            pk=int(user['userid']),
            username=user['login'],
            email=HTMLParser().unescape(user['usermail']),
            date_joined=datetime.fromtimestamp(user['registerdate']),
            logo="logo/{}".format(user['userlogo']),
            quote=HTMLParser().unescape(str(user['usercitation'])),
            website=HTMLParser().unescape(str(user['usersite'])),
        )
        u.set_password(password)
        u.save()
    print("Creating users... done{}".format(" "*20))
    with open('new_users.json', 'a') as f:
        json.dump(new_users, f)
    # TODO: SEND EMAILS WITH NEW PASSWORDS


def import_threads(f):
    cat_map = {1:1, 2:2, 3:3, 4:4, 5:6, 6:7, 7:5}  # mapping categories
    threads = json.loads(fix_json(f))
    # loading threads
    existing_threads = {}
    for thread in Thread.objects.iterator():
        existing_threads[thread.pk] = thread.category_id
    for i, thread in enumerate(threads):
        print("Creating threads... {}/{}".format(
            i+1, len(threads)), end="\r")
        if thread['idtopic'] in existing_threads: continue
        # prepare tokens for threads
        tokens = set()
        while len(tokens) != len(threads):
            tokens.add(keygen())
        isSticky = True if thread['postit'] == 1 else False
        t = Thread.objects.create(
            pk=int(thread['idtopic']),
            category=Category.objects.get(pk=cat_map[thread['idforum']]),
            title=HTMLParser().unescape(str(thread['sujet']))[:80],
            author=ForumUser.objects.get(pk=thread['idmembre']),
            icon=str(thread['icone'])+'.gif',
            viewCount=int(thread['nbvues']),
            isSticky=isSticky,
            cessionToken=tokens.pop()
        )
    print("Creating threads... done{}".format(" "*20))


def import_posts(f):

    def prepare_bulk(f):

        def clean_size(match_obj):
            return "[size=" + str(int(match_obj.group(1))+9) + "]"

        posts = json.loads(fix_json(f))
        # loading threads
        existing_threads = {}
        for thread in Thread.objects.iterator():
            existing_threads[thread.pk] = thread.category_id
        # loading posts
        existing_posts = set()
        for post in Post.objects.iterator():
            existing_posts.add(post.pk)
        post_counter = {}  # stores the number of posts per cat
        for category in Category.objects.all():  # initializing dict values
            post_counter[category.pk] = 0
        bulk = []
        for i, post in enumerate(posts):
            print("Preparing posts... {}/{}".format(
                i+1, len(posts)), end="\r")
            if post['parent'] not in existing_threads: continue
            # increment category post counter
            post_counter[existing_threads[post['parent']]] += 1
            if post['idpost'] in existing_posts: continue
            # perpare message
            content_plain = strip_tags(
                    HTMLParser().unescape(str(post['msg'])))
            # fix text size tags
            content_plain = re.sub(r'\[size=(\d)\]', clean_size, content_plain)
            # store prepared posts
            bulk.append(Post(
                pk=int(post['idpost']),
                thread_id=int(post['parent']),
                author_id=int(post['idmembre']),
                created=datetime.fromtimestamp(post['date']),
                content_plain=content_plain,
            ))
        return bulk, post_counter

    bulk, post_counter = prepare_bulk(f)
    print("\nCreating posts in the database...", end="\r")
    if bulk: Post.objects.bulk_create(bulk)
    print("Creating posts in the database... done")

    threads = Thread.objects.iterator()
    count = Thread.objects.count()
    for i, t in enumerate(threads):
        print('Updating threads... {}/{}'.format(
            i+1, count), end="\r")
        t.modified = t.latest_post.created
        for p in t.posts.iterator():
            t.contributors.add(p.author)
        t.save()
    print("Updating threads... done{}".format(" "*20))
    for key, value in post_counter.items():
        print('Updating post counter...', end="\r")
        c = Category.objects.get(pk=key)
        c.postCount = value
        c.save()
    print('Updating post counter... done')


def delete_inactive_users():
    delete_count = 0
    inactive_count = 0
    for u in ForumUser.objects.iterator():
        if not u.posts.exists():
            u.delete()
            delete_count += 1
        elif CUT_OFF_DATE > u.posts.latest().created:
            u.is_active = False
            u.save()
            inactive_count += 1
    print("Deleted {} users which never posted".format(delete_count))
    print("Deactivated {} users".format(inactive_count))


import_users(here('..', '..', '..', 'util', 'data', 'CF_user.json'))
import_threads(here('..', '..', '..', 'util', 'data', 'CF_topics.json'))
import_posts(here('..', '..', '..', 'util', 'data', 'CF_posts.json'))
delete_inactive_users()

cursor = connection.cursor()
cursor.execute('ALTER SEQUENCE user_forumuser_id_seq RESTART WITH {}'.format(
    ForumUser.objects.latest('pk').pk+1))
cursor.execute('ALTER SEQUENCE forum_thread_id_seq RESTART WITH {}'.format(
    Thread.objects.latest('pk').pk+1))
cursor.execute('ALTER SEQUENCE forum_post_id_seq RESTART WITH {}'.format(
    Post.objects.latest('pk').pk+1))
