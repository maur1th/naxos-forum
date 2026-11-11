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
