from django import forms
from django.contrib.auth.forms import UserCreationForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Submit

from .models import ForumUser

MAX_USERNAME_LENGTH = 20

# TODO
# Add email confirmation


class UniqueEmailMixin(object):

    def clean_email(self):
        """Ensure provided email addresses are unique in the db."""
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')  # For registration form
        if not username:                              # For other forms
            try:
                username = self.request.user
            except:  # Handle when Registration username is incorrect
                return email
        if email and ForumUser.objects.filter(email=email).exclude(
                username=username).count():
            raise forms.ValidationError('Adresse déjà enregistrée.')
        return email


class RestrictedImageField(forms.ImageField):
    def __init__(self, *args, **kwargs):
        self.max_upload_size = kwargs.pop('max_upload_size', None)
        super(RestrictedImageField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(RestrictedImageField, self).clean(*args, **kwargs)
        try:
            if data.size > self.max_upload_size:
                raise forms.ValidationError(
                    'La taille du fichier doit être inférieure à 100ko.')
        except AttributeError:
            pass
        return data


class RegisterForm(UniqueEmailMixin, UserCreationForm):
    email = forms.EmailField(required=True)

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


class UpdateUserForm(UniqueEmailMixin, forms.ModelForm):
    threadPaternityCode = forms.CharField(
        required=False, label='Obtenir la paternité d\'un sujet')

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.request = request
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('email'),
            Field('quote'),
            Field('website', placeholder="http://"),
            Field('showSmileys'),
            Field('logo', template="user/logoInput.html"),
            HTML('<label class="control-label">Autres préférences</label>'),
            Field('emailVisible'),
            Field('subscribeToEmails'),
            Field('mpEmailNotif'),
            # HTML('{% include "user/threadPaternity.html" %}'),
            Field('threadPaternityCode',
                  template="user/threadPaternityInput.html"),
        )

    class Meta:
        model = ForumUser
        fields = ('email', 'emailVisible', 'subscribeToEmails', 'mpEmailNotif',
                  'logo', 'quote', 'website', 'showSmileys')
