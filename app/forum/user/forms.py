from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, \
    AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.db import transaction
from django.template.defaultfilters import filesizeformat
from django.core.files.images import get_image_dimensions
from django.core.files.uploadedfile import UploadedFile
from django.urls import reverse

# Fix ugettext error: https://stackoverflow.com/a/75347232
import django
from django.utils.translation import gettext, gettext_lazy as _
django.utils.translation.ugettext = gettext

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Submit

from .models import ForumUser, TokenPool
from forum.models import BudgetRecord, Thread

MAX_USERNAME_LENGTH = 20
MAX_UPLOAD_SIZE = 102400
MAX_LENGTH = 120


class UniqueEmailMixin(object):

    def clean_email(self):
        """Ensure provided email addresses are unique in the db."""
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')  # For registration form
        if not username:                              # For other forms
            try:
                username = self.user
            except:  # Handle when Registration username is incorrect
                return email
        if email and ForumUser.objects.filter(email__iexact=email).exclude(
                username=username).count():
            raise forms.ValidationError('Adresse déjà enregistrée.')
        return email


class RegisterForm(UniqueEmailMixin, UserCreationForm):
    email = forms.EmailField(
        label=_('Email address'), required=True, help_text="Requis.")
    token = forms.CharField(
        max_length=50,
        label='Clé',
        help_text="Code unique requis pour créer un compte.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer'))

    class Meta:
        model = ForumUser
        fields = ('username', 'email', 'password1', 'password2')

    def clean_username(self):
        """
        UserCreationForm method where mentions of the User model are replaced
        by the custom AbstractUser model (here, ForumUser).
        https://code.djangoproject.com/ticket/19353
        and https://docs.djangoproject.com/en/1.7/_modules/django/contrib/
        auth/forms/#UserCreationForm
        """
        username = self.cleaned_data["username"]
        if len(username) > MAX_USERNAME_LENGTH:  # Additional check
            raise forms.ValidationError(
                str(MAX_USERNAME_LENGTH)+' caractères maximum.')
        try:
            ForumUser.objects.get(username=username)
        except ForumUser.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username']
        )

    def clean_token(self):
        token = self.cleaned_data["token"]
        if not TokenPool.objects.filter(token=token).exists():
            raise forms.ValidationError("Cette clé n'existe pas.")
        return token

    def save(self, commit=True):
        """
        Consume the invitation key and create the user in one transaction.

        The key is only deleted here, so a submission that fails validation
        leaves it usable. The DELETE's row count is what makes the key
        single-use: if a concurrent request already consumed it, nothing is
        deleted and the registration is refused.
        """
        if not commit:
            return super().save(commit=False)
        with transaction.atomic():
            deleted, _ = TokenPool.objects.filter(
                token=self.cleaned_data["token"]).delete()
            if not deleted:
                raise forms.ValidationError("Cette clé n'existe pas.")
            return super().save(commit=True)


class CrispyLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Connexion'))


class UpdateUserForm(UniqueEmailMixin, forms.ModelForm):
    token = forms.CharField(
        required=False,
        label='Obtenir la paternité d\'un sujet',
        help_text=("Si un autre membre vous a communiqué un code pour le "
                   "remplacer comme auteur de l'un de ses sujets, vous pouvez"
                   " en accepter la paternité en saisissant ce code.")
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')  # Used to ensure email is unique
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('email'),
            Field('quote'),
            Field('website', placeholder="http://"),
            Field('logo', template="user/logoInput.html"),
            HTML('<label class="control-label">Autres préférences</label>'),
            Field('emailVisible'),
            Field('showSmileys'),
            Field('fullscreen'),
            Field('showLogosOnSmartphone'),
            Field('token'),
        )

    def clean_token(self, *args, **kwargs):
        token = self.cleaned_data['token']
        if token and not Thread.objects.filter(cessionToken=token).exists():
            raise forms.ValidationError('Aucun sujet correspondant.')
        return token

    def clean_logo(self, *args, **kwargs):
        # Get image from form, return if no image was provided
        logo = self.cleaned_data['logo']
        # An unchanged avatar is a FieldFile, not an upload: nothing to check.
        # Checks run for every upload, including TemporaryUploadedFile (what
        # Django hands over above FILE_UPLOAD_MAX_MEMORY_SIZE).
        if not isinstance(logo, UploadedFile):
            return logo
        # Check file size (in ko)
        if logo.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError(
                ("Fichier trop volumineux. La taille maximale autorisée "
                 "est de {}.").format(filesizeformat(MAX_UPLOAD_SIZE)))
        # Check image size (in pixels)
        width, height = get_image_dimensions(logo)
        if width is None or height is None:
            raise forms.ValidationError("Image invalide.")
        if width > MAX_LENGTH or height > MAX_LENGTH:
            raise forms.ValidationError(
                ("Image trop grande. La taille maximale autorisée est de "
                 "{}x{} pixels.").format(MAX_LENGTH, MAX_LENGTH))
        return logo

    class Meta:
        model = ForumUser
        fields = ('email', 'emailVisible',
                  'logo', 'quote', 'website', 'showSmileys', 'fullscreen',
                  'showLogosOnSmartphone')


class CrispyPasswordForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user=user, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Modifier'))


class CrispyPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label=_('Email address'),
        max_length=254,
        help_text="Veuillez entrer l'adresse associée à votre compte."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Envoyer'))


class CrispySetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer'))


class BudgetRecordForm(forms.ModelForm):
    class Meta:
        model = BudgetRecord
        fields = ('label', 'amount')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('user:new_budget_record')
        self.helper.add_input(Submit('submit', 'Submit'))
