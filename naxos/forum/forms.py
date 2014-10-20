from django import forms

from .models import Post


class NewThreadForm(forms.ModelForm):
    title = forms.CharField(max_length=140)
    # icon = forms.ImageField(required=False)

    class Meta:
        model = Post
        fields = ('title', 'content_plain')
