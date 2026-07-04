from django.test import TestCase

from .models import ForumUser, TokenPool
from .forms import RegisterForm


class RegistrationTest(TestCase):

    def setUp(self):
        self.existing_user = ForumUser.objects.create_user(
            username='jacob', email='jacob@test.com', password='top_secret')
        # RegisterForm.clean_token requires a token that exists in TokenPool
        # (and consumes it). TokenPool.save() generates the value itself, so
        # read it back rather than passing one in.
        self.token = TokenPool.objects.create().token
        self.valid_form_data = {
            'username': 'test',
            'email': 'other@test.com',
            'password1': 'top_secret',
            'password2': 'top_secret',
            'token': self.token,
        }

    def test_email_in_use(self):
        form_data = {**self.valid_form_data, 'email': 'jacob@test.com'}
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['email'], ['Adresse déjà enregistrée.'])

    def test_valid_input(self):
        form = RegisterForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid(), form.errors.as_json())
