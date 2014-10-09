from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import ForumUser


# TODO
# Add email confirmation

class UniqueEmailMixin(object):

    def clean_email(self):
        "Ensure registered emails are unique."
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')  # For logged out forms
        try:                                          # For logged in forms
            username = self.user
        except:
            pass
        if email and ForumUser.objects.filter(email=email).exclude(
                username=username).count():
            raise forms.ValidationError('Adresse déjà enregistrée.')
        return email


class RegisterForm(UniqueEmailMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = ForumUser
        fields = ('username', 'email', 'password1', 'password2')

    def clean_username(self):
        """
        UserCreationForm method where mentions of the User model are replaced
        by the custom AbstractUser model (here, ForumUser).
        https://code.djangoproject.com/ticket/19353#no1
        and https://docs.djangoproject.com/en/1.7/_modules/django/contrib/
        auth/forms/#UserCreationForm
        """
        username = self.cleaned_data["username"]
        try:
            ForumUser.objects.get(username=username)
        except ForumUser.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )


class UpdateUserForm(UniqueEmailMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.user = user

    class Meta:
        model = ForumUser
        fields = ('email', 'emailVisible', 'subscribeToEmails', 'mpPopupNotif',
                  'mpEmailNotif', 'logo', 'quote', 'website')
