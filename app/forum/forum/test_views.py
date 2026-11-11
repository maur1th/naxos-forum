from django.test import TestCase
from django.urls import reverse

from user.models import ForumUser
from .models import Category, Thread, Post, Preview


class DeletedThreadTests(TestCase):
    """A deleted ("invisible") thread must not leak through any entry point."""

    def setUp(self):
        mk = ForumUser.objects.create_user
        self.author = mk('alice', 'a@example.com', 'pw')
        self.viewer = mk('bob', 'b@example.com', 'pw')
        self.cat = Category.objects.create(slug='general', title='General',
                                           subtitle='x')
        self.hidden = Thread.objects.create(
            title='Hidden thread', author=self.author, category=self.cat,
            personal=True)
        self.hidden_post = Post.objects.create(
            thread=self.hidden, author=self.author,
            content_plain='secretbody')
        self.open = Thread.objects.create(
            title='Open thread', author=self.author, category=self.cat)
        self.open_post = Post.objects.create(
            thread=self.open, author=self.author, content_plain='openbody')
        self.client.force_login(self.author)
        self.client.post(reverse('forum:delete_thread', args=[self.hidden.pk]))
        self.hidden.refresh_from_db()
        self.assertFalse(self.hidden.visible)
        self.client.force_login(self.viewer)

    def args(self, *extra):
        return (self.cat.slug, self.hidden.slug) + extra

    def test_post_detail(self):
        r = self.client.get(reverse('forum:post', args=[self.hidden_post.pk]))
        self.assertEqual(r.status_code, 404)

    def test_quote_of_hidden_post_from_other_thread(self):
        r = self.client.get(reverse(
            'forum:quote',
            args=[self.cat.slug, self.open.slug, self.hidden_post.pk]))
        self.assertEqual(r.status_code, 404)

    def test_quote_of_post_from_other_thread(self):
        other = Post.objects.create(
            thread=self.open, author=self.author, content_plain='x')
        t2 = Thread.objects.create(
            title='Third', author=self.author, category=self.cat)
        r = self.client.get(reverse(
            'forum:quote', args=[self.cat.slug, t2.slug, other.pk]))
        self.assertEqual(r.status_code, 404)

    def test_quote_in_visible_thread_still_works(self):
        r = self.client.get(reverse(
            'forum:quote',
            args=[self.cat.slug, self.open.slug, self.open_post.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'openbody')

    def test_post_search(self):
        r = self.client.get(reverse('forum:search'), {'q': 'post:secretb'})
        self.assertNotContains(r, 'secretbody')
        self.assertNotContains(r, 'Hidden thread')

    def test_post_search_finds_visible_posts(self):
        r = self.client.get(reverse('forum:search'), {'q': 'post:openb'})
        self.assertContains(r, 'Open thread')

    def test_new_post_get_and_post(self):
        url = reverse('forum:new_post', args=self.args())
        self.assertEqual(self.client.get(url).status_code, 404)
        r = self.client.post(url, {'content_plain': 'reply'})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.hidden.posts.count(), 1)

    def test_edit_post(self):
        self.client.force_login(self.author)
        url = reverse('forum:edit',
                      args=self.args(self.hidden_post.pk))
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_vote_poll(self):
        r = self.client.post(
            reverse('forum:vote', args=self.args()), {'choice_text': 'a'})
        self.assertEqual(r.status_code, 404)

    def test_top10(self):
        r = self.client.get(reverse('user:top10'))
        self.assertNotContains(r, 'Hidden thread')
        self.assertContains(r, 'Open thread')

    def test_category_status_ignores_hidden_threads(self):
        # Only the hidden thread is newer than the user's timestamp
        Thread.objects.filter(pk=self.open.pk).update(
            modified=self.hidden.modified.replace(year=2000))
        self.client.get(reverse('forum:top'))  # creates timestamps
        self.hidden.save()  # bump modified
        r = self.client.get(reverse('forum:top'))
        self.assertEqual(r.status_code, 200)


class PreviewOwnershipTests(TestCase):
    def setUp(self):
        mk = ForumUser.objects.create_user
        self.alice = mk('alice', 'a@example.com', 'pw')
        self.bob = mk('bob', 'b@example.com', 'pw')
        self.preview = Preview.objects.create(
            content_plain='draft text', author=self.alice)

    def test_other_member_cannot_open_or_consume_preview(self):
        self.client.force_login(self.bob)
        url = reverse('forum:preview', args=[self.preview.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertTrue(Preview.objects.filter(pk=self.preview.pk).exists())

    def test_author_can_open_once(self):
        self.client.force_login(self.alice)
        url = reverse('forum:preview', args=[self.preview.pk])
        self.assertContains(self.client.get(url), 'draft text')
        self.assertFalse(Preview.objects.filter(pk=self.preview.pk).exists())

    def test_legacy_preview_without_author_is_not_served(self):
        legacy = Preview.objects.create(content_plain='old')
        self.client.force_login(self.alice)
        r = self.client.get(reverse('forum:preview', args=[legacy.pk]))
        self.assertEqual(r.status_code, 404)
