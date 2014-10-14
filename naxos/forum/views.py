from django.views.generic import ListView, CreateView

from braces.views import LoginRequiredMixin

from .models import Category, Thread, Post
from .forms import ThreadFormSet
from user.models import ForumUser


class Welcome(LoginRequiredMixin, ListView):
    template_name = "forum/welcome.html"
    model = ForumUser


class TopView(LoginRequiredMixin, ListView):
    template_name = "forum/top.html"
    model = Category


class ThreadView(LoginRequiredMixin, ListView):
    template_name = "forum/threads.html"
    model = Thread

    def get_queryset(self):
        "Return only threads of the current category"
        return Thread.objects.filter(category=Category.objects.get(
            slug=self.kwargs['category_slug']))

    def get_context_data(self, **kwargs):
        "Pass Category from url to context"
        context = super(ThreadView, self).get_context_data(**kwargs)
        context['category'] = Category.objects.get(
            slug=self.kwargs['category_slug'])
        return context


class PostView(LoginRequiredMixin, ListView):
    template_name = "forum/posts.html"
    model = Post

    def get_queryset(self):
        return Post.objects.filter(thread=Thread.objects.get(
            slug=self.kwargs['thread_slug']))


class NewThread(LoginRequiredMixin, CreateView):
    form_class = ThreadFormSet
    # fields = ('title',)
    template_name = 'forum/new.html'

    # def get_form_kwargs(self):
    #     kwargs = super(NewThread, self).get_form_kwargs()
    #     kwargs.update({'author': self.request.user,
    #                    'category_slug': self.kwargs['category_slug']})
    #     return kwargs

    def get_context_data(self, **kwargs):
        "Pass Category from url to context"
        context = super(NewThread, self).get_context_data(**kwargs)
        context['author'] = ForumUser.objects.get(username=self.request.user)
        context['category'] = Category.objects.get(
            slug=self.kwargs['category_slug'])
        return context


class NewPost(LoginRequiredMixin, CreateView):
    model = Post
    fields = ()
    template_name = 'forum/new_post.html'
