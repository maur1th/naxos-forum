from django import forms
from django.forms.models import inlineformset_factory

# from user.models import ForumUser
from .models import Thread, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post


class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread

ThreadFormSet = inlineformset_factory(Thread, Post, extra=1)

# class NewThreadForm(forms.ModelForm):

#     def __init__(self, *args, **kwargs):
#         category = Category.objects.get(slug=kwargs.pop('category_slug'))
#         author = ForumUser.objects.get(username=kwargs.pop('author'))
#         super(NewThreadForm, self).__init__(*args, **kwargs)
#         self.category = category
#         self.author = author

#     def clean_author(self):
#         return self.author

#     class Meta:
#         model = Thread
#         fields = ('title',)
