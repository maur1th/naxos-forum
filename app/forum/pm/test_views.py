from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from user.models import ForumUser
from .models import Conversation, Message


class ConversationSearchTests(TestCase):

    def setUp(self):
        self.alice = ForumUser.objects.create_user(
            username='alice', email='alice@test.com', password='top_secret')
        self.bob = ForumUser.objects.create_user(
            username='bob', email='bob@test.com', password='top_secret')
        self.bobby = ForumUser.objects.create_user(
            username='bobby', email='bobby@test.com', password='top_secret')
        self.url = reverse('pm:search')
        self.client.force_login(self.alice)

    def make_conversation(self, other):
        c = Conversation.objects.create()
        c.participants.add(self.alice, other)
        return c

    def error_messages(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    def test_match_redirects_to_latest_message_of_conversation(self):
        c = self.make_conversation(self.bobby)
        Message.objects.create(conversation=c, author=self.alice,
                               content_plain='first')
        last = Message.objects.create(conversation=c, author=self.bobby,
                                      content_plain='last')

        # 'bobb' matches only bobby, not bob
        response = self.client.get(self.url, {'query': 'bobb'})

        self.assertRedirects(
            response,
            reverse('pm:msg', kwargs={'pk': c.pk}) + '?page=last#' + str(last.pk),
            fetch_redirect_response=False)

    def test_no_matching_user_shows_error(self):
        response = self.client.get(self.url, {'query': 'zed'})

        self.assertRedirects(response, reverse('pm:top'),
                             fetch_redirect_response=False)
        self.assertEqual(self.error_messages(response),
                         ['Aucun utilisateur trouvé.'])

    def test_several_matching_users_show_error(self):
        response = self.client.get(self.url, {'query': 'bob'})

        self.assertRedirects(response, reverse('pm:top'),
                             fetch_redirect_response=False)
        errors = self.error_messages(response)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith('Plusieurs utilisateurs possibles'))

    def test_request_without_query_does_not_error(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('pm:top'),
                             fetch_redirect_response=False)
        self.assertEqual(self.error_messages(response),
                         ['Aucun utilisateur trouvé.'])


class PMAccessTests(TestCase):
    def setUp(self):
        mk = ForumUser.objects.create_user
        self.alice = mk('alice', 'a@example.com', 'pw')
        self.bob = mk('bob', 'b@example.com', 'pw')
        self.outsider = mk('mallory', 'm@example.com', 'pw')
        self.conv = Conversation.objects.create()
        self.conv.participants.add(self.alice, self.bob)
        self.msg = Message.objects.create(
            conversation=self.conv, author=self.alice, content_plain='hi')

    def test_outsider_cannot_post(self):
        self.client.force_login(self.outsider)
        r = self.client.post(reverse('pm:new_msg', args=[self.conv.pk]),
                             {'content_plain': 'x'})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.conv.messages.count(), 1)

    def test_outsider_cannot_delete(self):
        self.client.force_login(self.outsider)
        r = self.client.post(reverse('pm:delete_msg', args=[self.msg.pk]))
        self.assertEqual(r.status_code, 404)
        self.msg.refresh_from_db()
        self.assertTrue(self.msg.shown)

    def test_outsider_cannot_switch_status(self):
        self.client.force_login(self.outsider)
        url = reverse('pm:switch_status', args=[self.conv.pk])
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertEqual(self.outsider.pmReadCaret.count(), 0)

    def test_participant_flow_and_empty_message(self):
        self.client.force_login(self.bob)
        url = reverse('pm:new_msg', args=[self.conv.pk])
        self.assertEqual(self.client.post(url, {}).status_code, 302)
        self.assertEqual(self.client.post(
            url, {'content_plain': '  '}).status_code, 302)
        self.assertEqual(self.conv.messages.count(), 1)
        self.client.post(url, {'content_plain': 'yo'})
        self.assertEqual(self.conv.messages.count(), 2)
        self.assertEqual(self.client.get(
            reverse('pm:msg', args=[self.conv.pk])).status_code, 200)
        # Bob cannot delete Alice's message
        r = self.client.post(reverse('pm:delete_msg', args=[self.msg.pk]))
        self.assertEqual(r.status_code, 404)
        self.msg.refresh_from_db()
        self.assertTrue(self.msg.shown)
        self.client.force_login(self.alice)
        self.client.post(reverse('pm:delete_msg', args=[self.msg.pk]))
        self.msg.refresh_from_db()
        self.assertFalse(self.msg.shown)

    def test_empty_conversation_does_not_error(self):
        empty = Conversation.objects.create()
        empty.participants.add(self.alice, self.bob)
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(
            reverse('pm:msg', args=[empty.pk])).status_code, 200)
        self.assertEqual(self.client.post(
            reverse('pm:switch_status', args=[empty.pk])).status_code, 302)
