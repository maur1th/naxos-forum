from django.core.exceptions import ValidationError
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

    def test_failed_submission_keeps_token(self):
        form_data = {**self.valid_form_data, 'password2': 'typo'}
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        self.assertTrue(TokenPool.objects.filter(token=self.token).exists())

        # Resubmitting with the corrected password succeeds with the same key
        form = RegisterForm(data=self.valid_form_data)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        form.save()
        self.assertFalse(TokenPool.objects.filter(token=self.token).exists())

    def test_token_cannot_create_two_accounts(self):
        first = RegisterForm(data=self.valid_form_data)
        second = RegisterForm(data={**self.valid_form_data,
                                    'username': 'other',
                                    'email': 'third@test.com'})
        # Both pass validation before either consumes the key (the race)
        self.assertTrue(first.is_valid(), first.errors.as_json())
        self.assertTrue(second.is_valid(), second.errors.as_json())
        first.save()
        with self.assertRaises(ValidationError):
            second.save()
        self.assertFalse(ForumUser.objects.filter(username='other').exists())

    def test_email_case_insensitive_uniqueness(self):
        form_data = {**self.valid_form_data, 'email': 'JACOB@Test.com'}
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['email'], ['Adresse déjà enregistrée.'])
