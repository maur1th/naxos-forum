from django.test import TestCase
from django.urls import reverse

from forum.models import Category, Thread
from .models import ForumUser


class AnonymousAccessTests(TestCase):
    """Every member-only page sends anonymous visitors to the login form."""

    def test_anonymous_users_are_redirected_to_login(self):
        urls = [
            reverse('user:profile'),
            reverse('user:password'),
            reverse('user:members'),
            reverse('user:top10'),
            reverse('user:budget'),
            reverse('user:new_budget_record'),
            reverse('forum:top'),
            reverse('forum:search'),
            reverse('forum:mentions'),
            reverse('pm:top'),
            reverse('pm:new_conv'),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(
                    response['Location'].startswith(reverse('user:login')),
                    response['Location'])


class MemberPagesTests(TestCase):

    def setUp(self):
        self.member = ForumUser.objects.create_user(
            username='member', email='member@test.com', password='top_secret')
        self.client.force_login(self.member)

    def test_member_pages_render(self):
        for name in ('user:profile', 'user:password', 'user:members',
                     'user:top10'):
            with self.subTest(name=name):
                self.assertEqual(
                    self.client.get(reverse(name)).status_code, 200)

    def test_budget_is_restricted(self):
        self.assertEqual(
            self.client.get(reverse('user:budget')).status_code, 403)
        self.assertEqual(
            self.client.post(reverse('user:new_budget_record')).status_code,
            403)

    def test_password_change_keeps_member_logged_in(self):
        response = self.client.post(reverse('user:password'), {
            'old_password': 'top_secret',
            'new_password1': 'a-much-longer-passphrase-42',
            'new_password2': 'a-much-longer-passphrase-42',
        })
        self.assertEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password(
            'a-much-longer-passphrase-42'))
        self.assertEqual(
            self.client.get(reverse('user:members')).status_code, 200)

    def test_top10_hides_deleted_threads(self):
        category = Category.objects.create(title='Cat', slug='cat')
        Thread.objects.create(
            title='Secret thread', slug='secret', category=category,
            author=self.member, visible=False)
        response = self.client.get(reverse('user:top10'))
        self.assertNotContains(response, 'Secret thread')


class NodeApiTests(TestCase):

    def test_post_is_refused(self):
        response = self.client.post(reverse('user:node_api'))
        self.assertEqual(response.status_code, 403)

    def test_unknown_session_is_refused(self):
        response = self.client.get(
            reverse('user:node_api'), {'sessionid': 'nope', 'status': 'x'})
        self.assertEqual(response.status_code, 403)
