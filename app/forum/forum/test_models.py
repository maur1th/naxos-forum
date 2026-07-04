import datetime

from django.test import TestCase
from django.utils import timezone

from user.models import ForumUser, Bookmark
from .models import Category, Thread, Post, UserMentions


class ForumTestMixin:
    """Shared fixtures: an author and a category."""

    def setUp(self):
        self.author = ForumUser.objects.create_user(
            username='alice', email='alice@test.com', password='top_secret')
        self.category = Category.objects.create(
            slug='general', title='General', subtitle='General chat')

    def make_thread(self, title='Hello World', author=None):
        return Thread.objects.create(
            title=title, author=author or self.author, category=self.category)


class ThreadSaveTests(ForumTestMixin, TestCase):

    def test_new_thread_slug_derives_from_title(self):
        self.assertEqual(self.make_thread(title='Hello World').slug, 'hello-world')

    def test_new_thread_gets_a_50_char_cession_token(self):
        thread = self.make_thread()
        self.assertEqual(len(thread.cessionToken), 50)

    def test_cession_tokens_are_unique_across_threads(self):
        t1 = self.make_thread(title='One')
        t2 = self.make_thread(title='Two')
        self.assertNotEqual(t1.cessionToken, t2.cessionToken)

    def test_duplicate_title_gets_a_distinct_slug_in_same_category(self):
        first = self.make_thread(title='Same Title')
        second = self.make_thread(title='Same Title')
        self.assertNotEqual(first.slug, second.slug)

    def test_untitled_thread_falls_back_to_sans_titre(self):
        # A title made only of punctuation slugifies to an empty string.
        thread = self.make_thread(title='!!!')
        self.assertTrue(thread.slug.startswith('sans-titre'))

    def test_cession_token_regenerates_when_author_changes(self):
        thread = self.make_thread()
        original = thread.cessionToken
        thread.author = ForumUser.objects.create_user(
            username='bob', email='bob@test.com', password='top_secret')
        thread.save()
        self.assertNotEqual(thread.cessionToken, original)

    def test_placeholder_tmp_token_is_regenerated_on_save(self):
        thread = self.make_thread()
        thread.cessionToken = 'tmp'
        thread.save()
        self.assertNotEqual(thread.cessionToken, 'tmp')
        self.assertEqual(len(thread.cessionToken), 50)

    def test_creating_a_thread_bookmarks_it_for_the_author(self):
        thread = self.make_thread()
        self.assertTrue(
            Bookmark.objects.filter(user=self.author, thread=thread).exists())


class PostSaveTests(ForumTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.thread = self.make_thread()

    def test_post_author_is_added_to_thread_contributors(self):
        bob = ForumUser.objects.create_user(
            username='bob', email='bob@test.com', password='top_secret')
        Post.objects.create(content_plain='hi', author=bob, thread=self.thread)
        self.assertIn(bob, self.thread.contributors.all())

    def test_new_post_bumps_thread_modified_to_post_created(self):
        # Push modified into the past without going through Thread.save().
        past = timezone.now() - datetime.timedelta(days=2)
        Thread.objects.filter(pk=self.thread.pk).update(modified=past)
        when = timezone.now()
        Post.objects.create(
            content_plain='hi', author=self.author, thread=self.thread, created=when)
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.modified, when)

    def test_editing_a_post_does_not_bump_thread_modified(self):
        post = Post.objects.create(
            content_plain='hi', author=self.author, thread=self.thread)
        self.thread.refresh_from_db()
        modified_after_create = self.thread.modified
        post.content_plain = 'edited'
        post.save()
        self.thread.refresh_from_db()
        self.assertEqual(self.thread.modified, modified_after_create)


class MentionSignalTests(ForumTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.thread = self.make_thread()

    def test_mentioning_a_user_records_it_and_flags_them(self):
        bob = ForumUser.objects.create_user(
            username='bob', email='bob@test.com', password='top_secret')
        self.assertFalse(bob.newMention)
        post = Post.objects.create(
            content_plain='hey @bob look at this',
            author=self.author, thread=self.thread)
        self.assertTrue(
            UserMentions.objects.filter(user=bob, post=post).exists())
        bob.refresh_from_db()
        self.assertTrue(bob.newMention)

    def test_mentioning_an_unknown_user_is_ignored(self):
        post = Post.objects.create(
            content_plain='hey @nobody', author=self.author, thread=self.thread)
        self.assertFalse(UserMentions.objects.filter(post=post).exists())


class PostCountTests(ForumTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.thread = self.make_thread()

    def test_thread_post_count_excludes_the_opening_post(self):
        for i in range(3):
            Post.objects.create(
                content_plain=f'post {i}', author=self.author, thread=self.thread)
        # post_count is posts.count() - 1 (the opening post is not counted).
        self.assertEqual(self.thread.post_count, 2)

    def test_category_post_count_totals_posts_across_threads(self):
        other = self.make_thread(title='Other')
        Post.objects.create(content_plain='a', author=self.author, thread=self.thread)
        Post.objects.create(content_plain='b', author=self.author, thread=other)
        self.assertEqual(self.category.post_count, 2)
