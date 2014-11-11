from django import forms
from django.core.urlresolvers import reverse
from django.forms.models import BaseInlineFormSet, inlineformset_factory

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Submit

from .models import Post, PollQuestion, PollChoice
from .util import get_title, rm_trailing_spaces

toolbar = "{% include \"toolbar.html\" %}"  # Text format


class GenericThreadForm(forms.ModelForm):

    title = forms.CharField(max_length=140, label='Titre')
    # icon = forms.ImageField(required=False)

    class Meta:
        model = Post
        fields = ('title', 'content_plain')


# Basic thread stuff
class ThreadForm(GenericThreadForm):

    def __init__(self, *args, **kwargs):
        c_slug = kwargs.pop('category_slug')
        # If editing an existing thread
        try:
            thread = kwargs.pop('thread')
            post = kwargs.pop('post')
            new = False
        except:
            new = True
        super(ThreadForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        if new:
            self.helper.form_action = reverse(
                'forum:new_thread', kwargs={'category_slug': c_slug})
            self.helper.layout = Layout(Field('title'),
                                        HTML(toolbar),
                                        Field('content_plain'))
        else:
            if post == thread.posts.first():  # Enable title edit if first post
                self.helper.layout = Layout(Field('title'),
                                            HTML(toolbar),
                                            Field('content_plain'))
            else:
                self.fields['title'].required = False
                self.helper.layout = Layout(Field('title', disabled=''),
                                            HTML(toolbar),
                                            Field('content_plain'))

            self.helper.form_action = reverse(
                'forum:edit', kwargs={'category_slug': c_slug,
                                      'thread_slug': thread.slug,
                                      'pk': post.pk})

        self.helper.add_input(Submit('submit', 'Enregistrer'))


class PostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.c_slug = kwargs.pop('category_slug')
        self.t = kwargs.pop('thread')
        super(PostForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'forum:new_post', kwargs={'category_slug': self.c_slug,
                                      'thread_slug': self.t.slug})
        self.helper.layout = Layout(HTML(get_title(self.t.title)),
                                    HTML(toolbar),
                                    Field('content_plain'))
        self.helper.add_input(Submit('submit', 'Enregistrer'))

    class Meta:
        model = Post
        fields = ('content_plain',)


# Polls stuff
class PollThreadForm(GenericThreadForm):

    def __init__(self, *args, **kwargs):
        super(PollThreadForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(Field('title'),
                                    HTML(toolbar),
                                    Field('content_plain'))
        self.helper.form_tag = False


class QuestionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    class Meta:
        model = PollQuestion
        fields = ('question_text',)
        labels = {'question_text': 'Question'}


class FormSetHelper(FormHelper):

    """Enables crispy forms for ChoicesFormSet"""

    def __init__(self, *args, **kwargs):
        super(FormSetHelper, self).__init__(*args, **kwargs)
        self.form_tag = False


class CustomCleanFormset(BaseInlineFormSet):

    def clean(self):
        super(CustomCleanFormset, self).clean()
        choices = list()
        for form in self.forms:
            try:
                choice_text = rm_trailing_spaces(
                    form.cleaned_data['choice_text'])
            except:
                continue  # Skip empty choice fields
            if choice_text in choices:
                msg = "Chaque choix doit être unique."
                raise forms.ValidationError(msg)
            else:
                choices.append(choice_text)


ChoicesFormSet = inlineformset_factory(
    PollQuestion,
    PollChoice,
    formset=CustomCleanFormset,
    fields=('choice_text',),
    labels={'choice_text': 'Choix'},
    can_delete=False,
    extra=10,
    min_num=2,
    max_num=10
)
