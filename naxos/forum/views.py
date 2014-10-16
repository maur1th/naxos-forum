from django.views.generic import ListView, CreateView
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect

from braces.views import LoginRequiredMixin

from .models import Category, Thread, Post
from .forms import NewThreadForm


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
        "Pass category from url to context"
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

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super(PostView, self).get_context_data(**kwargs)
        context['category'] = Category.objects.get(
            slug=self.kwargs['category_slug'])
        context['thread'] = Thread.objects.get(
            slug=self.kwargs['thread_slug'])
        return context


class NewThread(LoginRequiredMixin, CreateView):
    form_class = NewThreadForm
    template_name = 'forum/new_thread.html'

    def form_valid(self, form):
        thread = Thread()  # Create the Thread
        thread.title = self.request.POST['title']
        thread.author = self.request.user
        thread.category = Category.objects.get(
            slug=self.kwargs['category_slug'])
        thread.save()
        form.instance.thread = thread  # Complete the post
        form.instance.author = self.request.user
        form.instance.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        "Pass Category from url to context"
        context = super(NewThread, self).get_context_data(**kwargs)
        context['category'] = Category.objects.get(
            slug=self.kwargs['category_slug'])
        return context

    def get_success_url(self):
        return reverse_lazy('forum:category', kwargs=self.kwargs)


class NewPost(LoginRequiredMixin, CreateView):
    model = Post
    fields = ('content_plain',)
    template_name = 'forum/new_post.html'
