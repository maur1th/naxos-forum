from django import forms
from django.core.urlresolvers import reverse
from django.forms.models import BaseInlineFormSet, inlineformset_factory

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Submit
from crispy_forms.bootstrap import InlineRadios

from .models import Post, PollQuestion, PollChoice
from .util import get_title, rm_trailing_spaces

toolbar = "{% include \"toolbar.html\" %}"  # Text format


class GenericThreadForm(forms.ModelForm):

    CHOICES = (('1', 'icon1.gif',), ('2', 'icon2.gif',),
               ('3', 'icon3.gif',), ('4', 'icon4.gif',),
               ('5', 'icon5.gif',), ('6', 'icon6.gif',),
               ('7', 'icon7.gif',), ('8', 'icon8.gif',),
               ('9', 'icon9.gif',), ('10', 'icon10.gif',),
               ('11', 'icon11.gif',), ('12', 'icon12.gif',),
               ('13', 'icon13.gif',), ('14', 'icon14.gif',),
               ('15', 'icon15.gif',), ('16', 'icon16.gif',))
    title = forms.CharField(max_length=140, label='Titre')
    icon = forms.ChoiceField(widget=forms.RadioSelect,
        choices=CHOICES, label="Icône")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['icon'].initial = 1

    def clean_icon(self):
        return "icon" + self.cleaned_data['icon'] + ".gif"

    class Meta:
        model = Post
        fields = ('title', 'icon', 'content_plain')


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
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enregistrer'))
        self.helper.add_input(Submit('preview', 'Prévisualiser',))
        if new:  # This is a new thread
            self.helper.form_action = reverse(
                'forum:new_thread', kwargs={'category_slug': c_slug})
            self.helper.layout = Layout(Field('title'),
                                        InlineRadios('icon'),
                                        HTML(toolbar),
                                        Field('content_plain'))
        else:  # This is an edit
            if post == thread.posts.first():
                self.helper.layout = Layout(Field('title'),
                                            InlineRadios('icon'),
                                            HTML(toolbar),
                                            Field('content_plain'))
                self.helper.add_input(
                    Submit('cede', 'Céder le contrôle de ce sujet'))
            else:  # If it's not the first post
                self.fields['title'].required = False
                self.fields['icon'].required = False
                self.helper.layout = Layout(Field('title', disabled=''),
                                            HTML(toolbar),
                                            Field('content_plain'),
                                            Field('icon', type='hidden'),)
            self.helper.form_action = reverse(
                'forum:edit', kwargs={'category_slug': c_slug,
                                      'thread_slug': thread.slug,
                                      'pk': post.pk})


class PostForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.c_slug = kwargs.pop('category_slug')
        self.t = kwargs.pop('thread')
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse(
            'forum:new_post', kwargs={'category_slug': self.c_slug,
                                      'thread_slug': self.t.slug})
        self.helper.layout = Layout(HTML(get_title(self.t.title)),
                                    HTML(toolbar),
                                    Field('content_plain'))
        self.helper.add_input(Submit('submit', 'Enregistrer'))
        self.helper.add_input(Submit('preview', 'Prévisualiser',))

    class Meta:
        model = Post
        fields = ('content_plain',)


# Polls stuff
class PollThreadForm(GenericThreadForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(Field('title'),
                                    InlineRadios('icon'),
                                    HTML(toolbar),
                                    Field('content_plain'))
        self.helper.form_tag = False


class QuestionForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

    class Meta:
        model = PollQuestion
        fields = ('question_text',)
        labels = {'question_text': 'Question'}


class FormSetHelper(FormHelper):

    """Enables crispy forms for ChoicesFormSet"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False


class CustomCleanFormset(BaseInlineFormSet):

    def clean(self):
        super().clean()
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
