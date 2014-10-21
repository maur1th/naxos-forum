from django.views.generic import ListView, CreateView, UpdateView
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect

import datetime
from braces.views import LoginRequiredMixin

from .models import Category, Thread, Post
from .forms import ThreadForm


class TopView(LoginRequiredMixin, ListView):

    """Top view with all categories"""
    template_name = "forum/top.html"
    model = Category


class ThreadView(LoginRequiredMixin, ListView):

    """Display category list of threads"""
    template_name = "forum/threads.html"
    model = Thread
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        self.c = Category.objects.get(slug=self.kwargs['category_slug'])
        return super(ThreadView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        "Return threads of the current category ordered by latest post"
        return self.c.threads.all()

    def get_context_data(self, **kwargs):
        "Pass category from url to context"
        context = super(ThreadView, self).get_context_data(**kwargs)
        context['category'] = self.c
        return context


class PostView(LoginRequiredMixin, ListView):

    """Display thread list of posts"""
    template_name = "forum/posts.html"
    model = Post
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        c_slug = self.kwargs['category_slug']
        t_slug = self.kwargs['thread_slug']
        self.t = Thread.objects.get(slug=t_slug,
                                    category__slug=c_slug)
        return super(PostView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        "Return list of posts given thread and category slugs"
        return self.t.posts.all()

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super(PostView, self).get_context_data(**kwargs)
        context['category'] = self.t.category
        context['thread'] = self.t
        return context


class NewThread(LoginRequiredMixin, CreateView):
    form_class = ThreadForm
    template_name = 'forum/new_thread.html'

    def dispatch(self, request, *args, **kwargs):
        self.c = Category.objects.get(slug=self.kwargs['category_slug'])
        return super(NewThread, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        "Pass Category from url to context"
        context = super(NewThread, self).get_context_data(**kwargs)
        context['category'] = self.c
        return context

    def form_valid(self, form):
        "Handle thread and 1st post creation in the db"
        # Create the thread
        t = Thread.objects.create(
            title=self.request.POST['title'],
            author=self.request.user,
            category=self.c)
        # Complete the post and save it
        form.instance.thread = t
        form.instance.author = self.request.user
        form.instance.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('forum:category', kwargs=self.kwargs)


class NewPost(LoginRequiredMixin, CreateView):
    model = Post
    fields = ('content_plain',)
    template_name = 'forum/new_post.html'

    def dispatch(self, request, *args, **kwargs):
        c_slug = self.kwargs['category_slug']
        t_slug = self.kwargs['thread_slug']
        self.t = Thread.objects.get(slug=t_slug,
                                    category__slug=c_slug)
        return super(NewPost, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super(NewPost, self).get_context_data(**kwargs)
        context['category'] = self.kwargs['category_slug']
        context['thread'] = self.kwargs['thread_slug']
        return context

    def form_valid(self, form):
        """ Handle post creation in the db"""
        # Merge with previous thread if same author
        p = self.t.posts.latest()  # Get the latest post
        if p.author == self.request.user:
            p.content_plain += "\n\n{:s}".format(form.instance.content_plain)
            p.modified = datetime.datetime.now()
            p.save()
            self.t.modified, self.post_pk = p.modified, form.instance.pk
            return HttpResponseRedirect(self.get_success_url())
        else:
            form.instance.thread = self.t
            form.instance.author = self.request.user
            form.instance.save()
            self.t.modified = form.instance.created
            self.t.save()
            self.post_pk = form.instance.pk  # Store post pk for success url
            return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return (reverse_lazy('forum:thread', kwargs=self.kwargs)
                + '#' + str(self.post_pk))


class QuotePost(NewPost):

    """Quote the content of another post"""

    def dispatch(self, request, *args, **kwargs):
        self.p = Post.objects.get(pk=self.kwargs['pk'])
        return super(NewPost, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        "Pass quoted post content as initial data for form"
        initial = super(QuotePost, self).get_initial()
        text = "[quote][b]{:s} a dit :[/b]\n{:s}[/quote]".format(
            self.p.author.username, self.p.content_plain)
        initial['content_plain'] = text
        return initial


class EditPost(LoginRequiredMixin, UpdateView):
    form_class = ThreadForm
    model = Post
    template_name = 'forum/edit.html'

    def dispatch(self, request, *args, **kwargs):
        # Get the right post and thread
        self.p = Post.objects.get(pk=self.kwargs['pk'])
        self.t = self.p.thread
        return super(EditPost, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        "Pass thread title as initial data for form"
        initial = super(EditPost, self).get_initial()
        initial['title'] = self.t.title
        return initial

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super(EditPost, self).get_context_data(**kwargs)
        context['category_slug'] = self.kwargs['category_slug']
        context['thread'], context['post'] = self.t, self.p
        return context

    def form_valid(self, form):
        "Handle thread and 1st post creation in the db"
        # Edit thread title if indeed the first post
        if self.p == self.t.posts.first():
            self.t.title = self.request.POST['title']
        self.t.save()
        # Add modified datetime tag if needed
        if form.instance.content_plain != self.p.content_plain:
            form.instance.modified = datetime.datetime.now()
        # Save the post
        form.instance.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        pk = str(self.kwargs.pop('pk'))
        self.kwargs['thread_slug'] = self.t
        return (reverse_lazy('forum:thread', kwargs=self.kwargs)
                + '#' + pk)
