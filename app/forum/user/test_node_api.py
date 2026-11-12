from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.test import Client

from .models import ForumUser

SECRET = "test-secret"


@override_settings(
    NODE_API_SECRET=SECRET,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class NodeApiTests(TestCase):
    def setUp(self):
        self.user = ForumUser.objects.create_user(
            username="presence", email="p@example.org", password="pw12345!x")
        c = Client()
        c.login(username="presence", password="pw12345!x")
        self.sessionid = c.cookies["sessionid"].value
        self.url = reverse("user:node_api")
        self.key = f"user/{self.user.pk}/is_online"
        cache.delete(self.key)

    def post(self, data=None, secret=SECRET, **extra):
        headers = {"HTTP_X_NODE_SECRET": secret} if secret is not None else {}
        return self.client.post(self.url, data or {}, **headers, **extra)

    def test_connected_and_disconnected_toggle_presence(self):
        r = self.post({"sessionid": self.sessionid, "status": "connected"})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(cache.get(self.key))
        r = self.post({"sessionid": self.sessionid, "status": "disconnected"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(cache.get(self.key))

    def test_missing_or_wrong_secret_is_forbidden(self):
        data = {"sessionid": self.sessionid, "status": "connected"}
        self.assertEqual(self.post(data, secret=None).status_code, 403)
        self.assertEqual(self.post(data, secret="nope").status_code, 403)
        self.assertFalse(cache.get(self.key))

    @override_settings(NODE_API_SECRET=None)
    def test_unconfigured_secret_rejects_everything(self):
        r = self.post({"sessionid": self.sessionid, "status": "connected"}, secret="")
        self.assertEqual(r.status_code, 403)

    def test_get_is_not_allowed(self):
        r = self.client.get(
            self.url + f"?sessionid={self.sessionid}&status=connected",
            HTTP_X_NODE_SECRET=SECRET)
        self.assertEqual(r.status_code, 405)

    def test_bad_or_missing_status_is_400(self):
        self.assertEqual(self.post({"sessionid": self.sessionid}).status_code, 400)
        r = self.post({"sessionid": self.sessionid, "status": "whatever"})
        self.assertEqual(r.status_code, 400)

    def test_unknown_session_is_forbidden(self):
        r = self.post({"sessionid": "bogus", "status": "connected"})
        self.assertEqual(r.status_code, 403)
        r = self.post({"status": "connected"})
        self.assertEqual(r.status_code, 403)
