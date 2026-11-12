"""List pages run a fixed number of queries, whatever the number of rows."""
import datetime

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.paginator import Paginator
from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from pm.models import Conversation, Message
from user.models import Bookmark, CategoryTimeStamp, ForumUser
from .models import Category, Post, Thread
from .views import PostView, page_for_index

LOCMEM = {'default': {
    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    'LOCATION': 'test-queries',
}}


@override_settings(CACHES=LOCMEM)
class QueryCountTestCase(TestCase):

    def setUp(self):
        cache.clear()
        self.user = ForumUser.objects.create_user(
            username='reader', email='reader@test.com', password='pw')
        self.other = ForumUser.objects.create_user(
            username='writer', email='writer@test.com', password='pw')
        self.client.force_login(self.user)
        self.n = 0

    def tearDown(self):
        cache.clear()

    def count_queries(self, url):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return len(ctx), response

    def warm_count(self, url):
        """Queries of a second request, once per-object caches are warm."""
        self.client.get(url)
        return self.count_queries(url)[0]

    def make_thread(self, category, title, posts=1, author=None):
        author = author or self.other
        thread = Thread.objects.create(
            title=title, author=author, category=category)
        for i in range(posts):
            Post.objects.create(
                thread=thread, author=author, content_plain=f'post {i}')
        return thread


class PMListTests(QueryCountTestCase):
    url = reverse('pm:top')

    def conversation(self, other=None):
        if other is None:
            other = ForumUser.objects.create_user(
                username=f'pen{self.n}', email=f'pen{self.n}@test.com',
                password='pw')
            self.n += 1
        c = Conversation.objects.create()
        c.participants.add(self.user, other)
        return c

    def message(self, c, author, shown=True):
        return Message.objects.create(conversation=c, author=author,
                                      content_plain='hello', shown=shown)

    def add_conversations(self, n):
        for i in range(n):
            c = self.conversation()
            self.message(c, c.participants.exclude(pk=self.user.pk).get())
            m = self.message(c, self.user)
            if i % 2:
                self.user.pmReadCaret.add(m)

    def test_query_count_does_not_depend_on_conversations(self):
        self.add_conversations(2)
        self.assertEqual(self.warm_count(self.url), 8)
        self.add_conversations(8)
        self.assertEqual(self.warm_count(self.url), 8)

    def test_rows(self):
        read = self.conversation(self.other)
        self.message(read, self.other)
        self.user.pmReadCaret.add(self.message(read, self.user))

        unread = self.conversation()
        first_unread = self.message(unread, self.user)
        # read caret on an older message: the conversation is unread
        self.user.pmReadCaret.add(first_unread)
        latest_unread = self.message(unread, unread.participants.exclude(
            pk=self.user.pk).get())

        # the latest message was deleted: count and link skip it, but the
        # read caret still points at it
        deleted = self.conversation()
        kept = self.message(deleted, self.user)
        self.user.pmReadCaret.add(self.message(deleted, self.user, False))

        empty = self.conversation()
        self.message(empty, self.user, shown=False)

        response = self.client.get(self.url)
        rows = {c.pk: c for c in response.context['object_list']}
        self.assertEqual(
            {pk: (c.is_read, c.shown_count, c.latest_shown)
             for pk, c in rows.items()},
            {read.pk: (True, 2, read.messages.last()),
             unread.pk: (False, 2, latest_unread),
             deleted.pk: (True, 1, kept),
             empty.pk: (False, 0, None)})
        content = response.content.decode()
        self.assertIn(f'?page=last#{latest_unread.pk}"', content)
        self.assertIn(f'?page=last#{kept.pk}"', content)
        self.assertNotIn(reverse('pm:msg', args=[empty.pk]), content)
        self.assertIn('writer', content)
        self.assertEqual(content.count('img/unread.png'), 1 + 1)  # + legend


class CategoryListTests(QueryCountTestCase):
    url = reverse('forum:top')

    def add_categories(self, n):
        for i in range(n):
            c = Category.objects.create(
                slug=f'cat{self.n}', title=f'Cat {self.n}', subtitle='')
            self.n += 1
            self.make_thread(c, 'topic', posts=2)

    def test_query_count_does_not_depend_on_categories(self):
        self.add_categories(2)
        self.assertEqual(self.warm_count(self.url), 6)
        self.add_categories(7)
        self.assertEqual(self.warm_count(self.url), 6)

    def test_rows(self):
        news = Category.objects.create(slug='news', title='News', subtitle='')
        empty = Category.objects.create(slug='empty', title='E', subtitle='')
        hidden = Category.objects.create(slug='hidden', title='H', subtitle='')
        self.make_thread(news, 'old')
        self.make_thread(hidden, 'visible one')

        # the first visit records a timestamp for every category
        response = self.client.get(self.url)
        self.assertEqual(
            CategoryTimeStamp.objects.filter(user=self.user).count(), 3)
        self.assertEqual(
            [c.status for c in response.context['categories']],
            ['img/read.png'] * 3)

        latest = self.make_thread(news, 'new', posts=2)
        gone = self.make_thread(hidden, 'deleted')
        gone.visible = False
        gone.save()

        response = self.client.get(self.url)
        categories = {c.slug: c for c in response.context['categories']}
        self.assertEqual(categories['news'].status, 'img/unread.png')
        self.assertEqual(categories['empty'].status, 'img/read.png')
        self.assertEqual(categories['hidden'].status, 'img/read.png')
        self.assertEqual(categories['news'].thread_count, 2)
        self.assertIsNone(categories['empty'].latest_thread)
        self.assertEqual(categories['news'].latest_thread, latest)
        self.assertEqual(categories['hidden'].latest_thread.title,
                         'visible one')
        content = response.content.decode()
        last_post = latest.posts.last()
        self.assertIn(
            '{}?page=last#{}'.format(
                reverse('forum:thread', args=['news', latest.slug]),
                last_post.pk),
            content)
        self.assertNotIn(gone.slug, content)


class ThreadListTests(QueryCountTestCase):

    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(
            slug='general', title='General', subtitle='')
        self.url = reverse('forum:category', args=['general'])

    def add_threads(self, n):
        old = timezone.now() - datetime.timedelta(days=1)
        for i in range(n):
            t = self.make_thread(self.category, f'topic {self.n}', posts=3)
            self.n += 1
            if i % 2:
                # Read up to the first post, so the rest is unread
                Bookmark.objects.create(user=self.user, thread=t)
                Bookmark.objects.filter(user=self.user, thread=t)\
                    .update(timestamp=old)
                t.posts.update(created=timezone.now())
            if i % 3 == 0:
                Post.objects.create(thread=t, author=self.user,
                                    content_plain='me too')
        cache.delete(f'bookmark/{self.user.pk}')

    def cold_status_count(self):
        """Queries when every thread's read status must be recomputed."""
        self.client.get(self.url)
        reset = ForumUser.objects.get(pk=self.user.pk).resetDateTime
        for t in Thread.objects.all():
            cache.delete(make_template_fragment_key(
                'thread_status', [t.pk, self.user.pk, reset]))
        return self.count_queries(self.url)[0]

    def test_query_count_does_not_depend_on_threads(self):
        self.add_threads(2)
        self.assertEqual(self.cold_status_count(), 8)
        self.add_threads(10)
        self.assertEqual(self.cold_status_count(), 8)

    def test_status_icons_and_bookmark_links(self):
        start = timezone.now() - datetime.timedelta(days=1)

        def at(minutes):
            return start + datetime.timedelta(minutes=minutes)

        # 35 posts, read up to the 31st: the first unread post (32nd) is on
        # page 2, which also holds the two orphans
        long = self.make_thread(self.category, 'long', posts=35)
        posts = list(long.posts.order_by('pk'))
        for i, p in enumerate(posts):
            Post.objects.filter(pk=p.pk).update(created=at(i))
        Thread.objects.filter(pk=long.pk).update(modified=at(34))
        Bookmark.objects.create(user=self.user, thread=long)
        Bookmark.objects.filter(thread=long).update(timestamp=at(30))

        # contributed and read since
        mine = self.make_thread(self.category, 'mine', author=self.user)
        Thread.objects.filter(pk=mine.pk).update(modified=at(1))

        # never opened
        fresh = self.make_thread(self.category, 'fresh')
        Thread.objects.filter(pk=fresh.pk).update(modified=at(2))
        cache.delete(f'bookmark/{self.user.pk}')

        response = self.client.get(self.url)
        rows = {t.pk: t for t in response.context['object_list']}
        self.assertEqual(rows[long.pk].status, 'img/unread.png')
        self.assertEqual(rows[long.pk].page, 2)
        self.assertEqual(rows[long.pk].bookmark.pk, posts[31].pk)
        self.assertEqual(rows[mine.pk].status, 'img/read_contributor.png')
        self.assertIsNone(rows[mine.pk].bookmark)
        self.assertEqual(rows[fresh.pk].status, 'img/unread.png')
        self.assertEqual((rows[fresh.pk].bookmark, rows[fresh.pk].page),
                         (True, 1))
        content = response.content.decode()
        self.assertIn('{}?page=2#{}'.format(
            reverse('forum:thread', args=['general', long.slug]),
            posts[31].pk), content)


class MemberListTests(QueryCountTestCase):

    def test_query_count_does_not_depend_on_members(self):
        url = reverse('user:members')
        self.assertEqual(self.count_queries(url)[0], 2)
        category = Category.objects.create(slug='c', title='C', subtitle='')
        for i in range(6):
            u = ForumUser.objects.create_user(
                username=f'm{i}', email=f'm{i}@test.com', password='pw',
                is_active=bool(i % 2))
            self.make_thread(category, f't{i}', author=u)
        self.assertEqual(self.count_queries(url)[0], 2)

    def test_last_post_and_online(self):
        category = Category.objects.create(slug='c', title='C', subtitle='')
        thread = self.make_thread(category, 't')
        Post.objects.filter(thread=thread).update(
            created=timezone.make_aware(datetime.datetime(2020, 3, 4, 12)))
        cache.set(f'user/{self.user.pk}/is_online', True)
        response = self.client.get(reverse('user:members'))
        members = {m.username: m for m in response.context['active_users']}
        self.assertTrue(members['reader'].online)
        self.assertFalse(members['writer'].online)
        self.assertIn('dernier post le 04/03/20', response.content.decode())


class MentionAutocompleteTests(QueryCountTestCase):

    def setUp(self):
        super().setUp()
        category = Category.objects.create(slug='c', title='C', subtitle='')
        thread = self.make_thread(category, 't')
        self.url = reverse('forum:thread', args=['c', thread.slug])

    def test_thread_page_does_not_load_user_rows(self):
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(self.url)
        user_list = [q['sql'] for q in ctx
                     if 'LOWER("user_forumuser"."username")' in q['sql']]
        self.assertEqual(len(user_list), 1)
        self.assertNotIn('"password"', user_list[0])
        # cached afterwards
        with CaptureQueriesContext(connection) as ctx:
            self.client.get(self.url)
        self.assertFalse([q for q in ctx
                          if 'LOWER("user_forumuser"."username")' in q['sql']])

    def test_list_follows_registrations_and_deactivations(self):
        users = lambda: self.client.get(self.url).context['users']
        self.assertEqual(users(), ['@reader', '@writer'])
        ForumUser.objects.create_user(
            username='Alice', email='alice@test.com', password='pw')
        self.assertEqual(users(), ['@Alice', '@reader', '@writer'])
        self.other.is_active = False
        self.other.save()
        self.assertEqual(users(), ['@Alice', '@reader'])
        self.other.is_active = True
        self.other.save()
        self.assertEqual(users(), ['@Alice', '@reader', '@writer'])


class PageForIndexTests(SimpleTestCase):

    def test_matches_paginator(self):
        per_page = PostView.paginate_by
        for count in range(1, 4 * per_page):
            paginator = Paginator(range(count), per_page,
                                  orphans=PostView.paginate_orphans)
            for index in range(count):
                expected = next(
                    n for n in paginator.page_range
                    if index in paginator.page(n).object_list)
                self.assertEqual(page_for_index(index, count), expected,
                                 (index, count))
