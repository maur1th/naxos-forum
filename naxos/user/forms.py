from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, \
    AuthenticationForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Submit

from .models import ForumUser

MAX_USERNAME_LENGTH = 20


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
    email = forms.EmailField(required=True)

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


class CrispyAuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Connexion'))


class UpdateUserForm(UniqueEmailMixin, forms.ModelForm):
    threadPaternityCode = forms.CharField(
        required=False, label='Obtenir la paternité d\'un sujet')

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
            Field('threadPaternityCode',
                  template="user/threadPaternityInput.html"),
        )

    class Meta:
        model = ForumUser
        fields = ('email', 'emailVisible', 'subscribeToEmails', 'mpEmailNotif',
                  'logo', 'quote', 'website', 'showSmileys')


class CrispyPasswordForm(PasswordChangeForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user=user, *args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Modifier'))


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
