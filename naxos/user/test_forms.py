from django.contrib.auth.models import User
from django.test import TestCase

from .forms import RegisterForm


class RegistrationTest(TestCase):

    def setUp(self):
        User.objects.create_user(username='jacob',
                                 email='jacob@test.com', password='top_secret')

    def test_email_in_use(self):
        form_data = {
            'username': 'test',
            'email': 'jacob@test.com',
            'password1': 'top_secret',
            'password2': 'top_secret'
        }
        form = RegisterForm(data=form_data)
        self.assertEqual(form.errors['email'], ['Adresse déjà enregistrée.'])

    def test_valid_input(self):
        form_data = {
            'username': 'test',
            'email': 'other@test.com',
            'password1': 'top_secret',
            'password2': 'top_secret'
        }
        form = RegisterForm(data=form_data)
        self.assertEqual(form.is_valid(), True)
