from django.test import TestCase
from django.urls import reverse

from user.models import ForumUser
from .models import Conversation, Message


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
        self.client.post(reverse('pm:delete_msg', args=[self.msg.pk]))
        self.msg.refresh_from_db()
        self.assertFalse(self.msg.shown)
