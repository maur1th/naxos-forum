import io
import os

from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import (InMemoryUploadedFile,
                                            TemporaryUploadedFile)
from django.test import TestCase

from .models import ForumUser, TokenPool
from .forms import RegisterForm, UpdateUserForm


def png_bytes(width, height, noise=False):
    """PNG data; `noise` makes the file large, a solid colour keeps it small."""
    if noise:
        image = Image.frombytes('RGB', (width, height),
                                os.urandom(width * height * 3))
    else:
        image = Image.new('RGB', (width, height))
    buf = io.BytesIO()
    image.save(buf, 'PNG')
    return buf.getvalue()


def upload(data, spooled):
    """Build an upload the way Django does: spooled to disk or in memory."""
    if spooled:
        # FILE_UPLOAD_MAX_MEMORY_SIZE is exceeded: Django uses a temp file.
        f = TemporaryUploadedFile('avatar.png', 'image/png', len(data), None)
        f.write(data)
        f.seek(0)
        return f
    return InMemoryUploadedFile(io.BytesIO(data), 'logo', 'avatar.png',
                                'image/png', len(data), None)


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


class AvatarLimitsTest(TestCase):

    def setUp(self):
        self.user = ForumUser.objects.create_user(
            username='jacob', email='jacob@test.com', password='top_secret')

    def submit(self, logo):
        form = UpdateUserForm(data={'email': self.user.email},
                              files={'logo': logo} if logo else {},
                              instance=self.user, user=self.user)
        return form, form.is_valid()

    def assertRejected(self, data, spooled, message):
        form, valid = self.submit(upload(data, spooled))
        self.assertFalse(valid)
        self.assertIn(message, form.errors['logo'][0])

    def assertAccepted(self, data, spooled):
        form, valid = self.submit(upload(data, spooled))
        self.assertTrue(valid, form.errors.as_json())

    def test_oversized_image_rejected_in_memory(self):
        self.assertRejected(png_bytes(3000, 3000), False, 'Image trop grande')

    def test_oversized_image_rejected_when_spooled_to_disk(self):
        # Regression: uploads above FILE_UPLOAD_MAX_MEMORY_SIZE skipped checks
        self.assertRejected(png_bytes(3000, 3000), True, 'Image trop grande')

    def test_heavy_file_rejected_when_spooled_to_disk(self):
        # 400x400 noise is ~480 KB: over the 100 KB limit
        self.assertRejected(png_bytes(400, 400, noise=True), True,
                            'Fichier trop volumineux')

    def test_heavy_file_rejected_in_memory(self):
        self.assertRejected(png_bytes(400, 400, noise=True), False,
                            'Fichier trop volumineux')

    def test_valid_avatar_accepted_in_memory_and_on_disk(self):
        self.assertAccepted(png_bytes(120, 120), False)
        self.assertAccepted(png_bytes(120, 120), True)

    def test_unchanged_avatar_is_kept_on_save(self):
        self.user.logo = 'logo/existing.png'
        self.user.save()
        form = UpdateUserForm(data={'email': 'new@test.com'},
                              instance=self.user, user=self.user)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        form.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.logo.name, 'logo/existing.png')
