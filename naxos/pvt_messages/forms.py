from django import forms
from .models import Conversation


class ConversationForm(forms.ModelForm):
    class Meta:
        model = Conversation
