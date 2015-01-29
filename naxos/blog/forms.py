from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import Post


class PostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.add_input(Submit('submit', 'Enregistrer'))

    class Meta:
        model = Post
        fields = ['title', 'content', 'image']
