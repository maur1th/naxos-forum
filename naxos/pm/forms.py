from django import forms
from .models import Message

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Submit

from user.models import ForumUser

toolbar = "{% include \"toolbar.html\" %}"  # Text formatting


class ConversationForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(label="Destinataire",
                                       queryset=ForumUser.objects.none(),
                                       initial="",
                                       widget=forms.Select())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['recipient'].queryset = ForumUser.objects.exclude(
            username=user)
        self.helper = FormHelper()
        self.helper.layout = Layout(Field('recipient'),
                                    HTML(toolbar),
                                    Field('content_plain'))
        self.helper.add_input(Submit('submit', 'Envoyer'))

    class Meta:
        model = Message
        fields = ('recipient', 'content_plain')
