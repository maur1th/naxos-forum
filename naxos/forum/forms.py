from django import forms

from .models import Post


class ThreadForm(forms.ModelForm):
    title = forms.CharField(max_length=140, label='Titre')
    # icon = forms.ImageField(required=False)

    class Meta:
        model = Post
        fields = ('title', 'content_plain')
