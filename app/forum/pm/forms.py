from django import forms
from .models import Message

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Submit

from user.models import ForumUser


toolbar = "{% include \"toolbar.html\" %}"  # Text formatting


def get_user_list(user_pk):
    q = ForumUser.objects.exclude(pk=user_pk)\
                         .exclude(is_active=False)\
                         .extra(select={'username_lower': 'lower(username)'})\
                         .order_by('username_lower')
    return q


class ConversationForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(label="Destinataire",
                                       queryset=ForumUser.objects.none(),
                                       initial=0,
                                       widget=forms.Select())

    def __init__(self, *args, **kwargs):
        user, initial = kwargs.pop('user'), kwargs.pop('recipient')
        super().__init__(*args, **kwargs)
        # Exclude author from available recipients so no cleaning needed
        self.fields['recipient'].queryset = get_user_list(user)
        # Update recipient field initial value from kwargs
        self.fields['recipient'].initial = initial
        self.helper = FormHelper()
        self.helper.layout = Layout(Field('recipient'),
                                    HTML(toolbar),
                                    Field('content_plain'))
        self.helper.add_input(Submit('submit', 'Envoyer'))

    class Meta:
        model = Message
        fields = ('recipient', 'content_plain')
