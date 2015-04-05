from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, \
    AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.template.defaultfilters import filesizeformat
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import ugettext, ugettext_lazy as _

from PIL import Image
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Submit

from .models import ForumUser, TokenPool
from forum.models import ThreadCession

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
        if email and ForumUser.objects.filter(email=email).exclude(
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
        token = TokenPool.objects.filter(token=self.cleaned_data["token"])
        if not token.exists():
            raise forms.ValidationError("Cette clé n'existe pas.")
        else:
            token.delete()


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
            Field('subscribeToEmails'),
            Field('mpEmailNotif'),
            Field('showSmileys'),
            Field('fullscreen'),
            Field('token'),
        )

    def clean_token(self, *args, **kwargs):
        token = self.cleaned_data['token']
        if token and not ThreadCession.objects.filter(token=token).exists():
            raise forms.ValidationError('Aucun sujet correspondant.')
        return token

    def clean_logo(self, *args, **kwargs):
        # Get image from form, return if no image was provided
        logo = self.cleaned_data['logo']
        if type(logo) is not InMemoryUploadedFile:
            return logo
        # Check image size (in pixels)
        img = Image.open(logo)
        for length in img.size:
            if length > MAX_LENGTH:
                raise forms.ValidationError(
                    ("Image trop grande. La taille maximale autorisée est de "
                     "{}x{} pixels.").format(MAX_LENGTH,MAX_LENGTH))
        # Check image size (in ko)
        if logo._size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError(
                ("Fichier trop volumineux. La taille maximale autorisée "
                 "est de {}.").format(filesizeformat(MAX_UPLOAD_SIZE)))
        return logo

    class Meta:
        model = ForumUser
        fields = ('email', 'emailVisible', 'subscribeToEmails', 'mpEmailNotif',
                  'logo', 'quote', 'website', 'showSmileys', 'fullscreen')


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


class RestrictedImageField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        self.max_upload_size = kwargs.pop('max_upload_size', None)
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        try:
            if data.size > self.max_upload_size:
                raise forms.ValidationError(
                    'La taille du fichier doit être inférieure à 100ko.')
        except AttributeError:
            pass
        return data
