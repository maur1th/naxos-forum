import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from user.models import ForumUser
from .models import Category, Thread, Post


class ReplyFloodCheckTests(TestCase):
    """Reply, quote and the 5-second anti-flood check in PostForm."""

    def setUp(self):
        self.author = ForumUser.objects.create_user(
            username='alice', email='alice@test.com', password='top_secret')
        self.category = Category.objects.create(
            slug='general', title='General', subtitle='General chat')
        self.thread = Thread.objects.create(
            title='Hello World', author=self.author, category=self.category)
        self.newbie = ForumUser.objects.create_user(
            username='newbie', email='n@test.com', password='pw')

    def reply_url(self):
        return reverse('forum:new_post',
                       args=[self.category.slug, self.thread.slug])

    def test_first_reply_of_a_new_member(self):
        self.client.force_login(self.newbie)
        r = self.client.post(self.reply_url(), {'content_plain': 'hello'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.thread.posts.count(), 1)

    def test_first_quote_of_a_new_member(self):
        original = Post.objects.create(
            content_plain='original', author=self.author, thread=self.thread)
        self.client.force_login(self.newbie)
        url = reverse('forum:quote', args=[
            self.category.slug, self.thread.slug, original.pk])
        r = self.client.post(url, {'content_plain': 'quoted reply'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.thread.posts.count(), 2)

    def test_second_reply_within_five_seconds_is_rejected(self):
        self.client.force_login(self.newbie)
        self.client.post(self.reply_url(), {'content_plain': 'first'})
        r = self.client.post(self.reply_url(), {'content_plain': 'second'})
        self.assertEqual(r.status_code, 200)
        self.assertIn('form', r.context)
        self.assertFalse(r.context['form'].is_valid())
        self.assertEqual(self.thread.posts.count(), 1)

    def test_reply_after_five_seconds_is_accepted(self):
        Post.objects.create(
            content_plain='old', author=self.newbie, thread=self.thread,
            created=timezone.now() - datetime.timedelta(seconds=10))
        self.client.force_login(self.newbie)
        r = self.client.post(self.reply_url(), {'content_plain': 'later'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.thread.posts.count(), 2)


class SecurityHeadersTests(TestCase):
    def test_pages_cannot_be_framed(self):
        r = self.client.get(reverse('user:login'))
        self.assertEqual(r['X-Frame-Options'], 'DENY')
