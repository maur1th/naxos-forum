from django import forms

from .models import Post


class ThreadForm(forms.ModelForm):
    title = forms.CharField(max_length=140, label='Titre')
    # icon = forms.ImageField(required=False)

    class Meta:
        model = Post
        fields = ('title', 'content_plain')


class PollForm(forms.Form):
    question = forms.CharField(max_length=80)

    def __init__(self, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        extra = kwargs.pop('extra')

        for i, values in enumerate(extra):
            pass
