from django import forms
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import Post


class ThreadForm(forms.ModelForm):
    title = forms.CharField(max_length=140, label='Titre')
    # icon = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        c_slug = kwargs.pop('category_slug')
        super(ThreadForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_method = 'post'
        self.helper.form_action = reverse(
            'forum:new_thread', kwargs={'category_slug': c_slug})

        self.helper.add_input(Submit('submit', 'Enregistrer'))

    class Meta:
        model = Post
        fields = ('title', 'content_plain')


class PostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.c_slug = kwargs.pop('category_slug')
        try:
            self.t_slug = kwargs.pop('thread_slug')
        except:
            pass
        super(PostForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_method = 'post'
        self.helper.form_action = reverse(
            'forum:new_post', kwargs={'category_slug': self.c_slug,
                                      'thread_slug': self.t_slug})

        self.helper.add_input(Submit('submit', 'Enregistrer'))

    class Meta:
        model = Post
        fields = ('content_plain',)


class PollForm(forms.Form):
    question = forms.CharField(max_length=80)

    def __init__(self, *args, **kwargs):
        super(PollForm, self).__init__(*args, **kwargs)
        extra = kwargs.pop('extra')

        for i, values in enumerate(extra):
            pass
