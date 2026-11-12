import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from user.models import ForumUser
from .models import Category, Thread, Post, Preview, PollQuestion, \
    PollChoice


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

    def test_referrer_sent_to_same_origin(self):
        # no-referrer makes browsers send "Origin: null" on form posts,
        # which fails Django's CSRF origin check.
        r = self.client.get(reverse('user:login'))
        self.assertEqual(r['Referrer-Policy'], 'same-origin')


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
            reverse('forum:vote', args=self.args()), {'choice': '1'})
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
        Thread.objects.filter(pk=self.hidden.pk).update(
            modified=timezone.now() + datetime.timedelta(days=1))
        r = self.client.get(reverse('forum:top'))
        status = {c.pk: c.status for c in r.context['categories']}
        self.assertEqual(status[self.cat.pk], 'img/read.png')


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

    def test_poll_preview_belongs_to_author(self):
        cat = Category.objects.create(slug='polls', title='Polls',
                                      subtitle='x')
        self.client.force_login(self.alice)
        r = self.client.post(
            reverse('forum:new_poll', args=[cat.slug]),
            {'preview': '1', 'thread-content_plain': 'poll draft'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Preview.objects.filter(
            author=self.alice, content_plain='poll draft').exists())

    def test_legacy_preview_without_author_is_not_served(self):
        legacy = Preview.objects.create(content_plain='old')
        self.client.force_login(self.alice)
        r = self.client.get(reverse('forum:preview', args=[legacy.pk]))
        self.assertEqual(r.status_code, 404)


class VotePollTests(TestCase):
    def setUp(self):
        self.alice = ForumUser.objects.create_user(
            username='alice', email='alice@test.com', password='pw')
        self.bob = ForumUser.objects.create_user(
            username='bob', email='bob@test.com', password='pw')
        self.cat = Category.objects.create(
            slug='general', title='General', subtitle='x')
        self.thread = Thread.objects.create(
            title='Poll', author=self.alice, category=self.cat)
        self.question = PollQuestion.objects.create(
            question_text='q', thread=self.thread)
        self.a = PollChoice.objects.create(question=self.question,
                                           choice_text='a')
        self.b = PollChoice.objects.create(question=self.question,
                                           choice_text='b')
        self.plain = Thread.objects.create(
            title='Plain', author=self.alice, category=self.cat)
        self.url = reverse('forum:vote', args=[self.cat.slug,
                                               self.thread.slug])
        self.client.force_login(self.bob)

    def totals(self):
        votes = sum(PollChoice.objects.values_list('votes', flat=True))
        return votes, self.question.voters.count()

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_thread_without_poll(self):
        url = reverse('forum:vote', args=[self.cat.slug, self.plain.slug])
        self.assertEqual(
            self.client.post(url, {'choice': self.a.pk}).status_code, 404)

    def test_unknown_or_foreign_choice(self):
        other = PollQuestion.objects.create(
            question_text='o', thread=self.plain)
        foreign = PollChoice.objects.create(question=other, choice_text='z')
        for value in ('nope', '', '999999', str(foreign.pk)):
            r = self.client.post(self.url, {'choice': value})
            self.assertEqual(r.status_code, 302)
        self.assertEqual(self.totals(), (0, 0))
        self.assertEqual(PollChoice.objects.get(pk=foreign.pk).votes, 0)

    def test_hidden_thread_refuses_votes(self):
        Thread.objects.filter(pk=self.thread.pk).update(visible=False)
        r = self.client.post(self.url, {'choice': self.a.pk})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.totals(), (0, 0))

    def test_double_vote_counts_once(self):
        self.client.post(self.url, {'choice': self.a.pk})
        self.client.post(self.url, {'choice': self.b.pk})
        self.assertEqual(self.totals(), (1, 1))
        self.assertEqual(PollChoice.objects.get(pk=self.a.pk).votes, 1)

    def test_votes_match_voters(self):
        self.client.post(self.url, {'choice': self.a.pk})
        self.client.force_login(self.alice)
        self.client.post(self.url, {'choice': self.b.pk})
        self.assertEqual(self.totals(), (2, 2))
