from django.views.generic import ListView, CreateView, UpdateView
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect

from braces.views import LoginRequiredMixin

from .models import Category, Thread, Post
from .forms import ThreadForm


class TopView(LoginRequiredMixin, ListView):
    template_name = "forum/top.html"
    model = Category


class ThreadView(LoginRequiredMixin, ListView):
    template_name = "forum/threads.html"
    model = Thread

    def get_queryset(self):
        "Return threads of the current category ordered by latest post"
        c_slug = self.kwargs['category_slug']
        return Thread.objects.filter(category__slug=c_slug)

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
        "Return list of posts given thread and category slugs"
        c_slug = self.kwargs['category_slug']
        t_slug = self.kwargs['thread_slug']
        return Post.objects.filter(thread__slug=t_slug,
                                   thread__category__slug=c_slug)

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super(PostView, self).get_context_data(**kwargs)
        c_slug = self.kwargs['category_slug']
        t_slug = self.kwargs['thread_slug']
        context['category'] = Category.objects.get(slug=c_slug)
        context['thread'] = Thread.objects.get(slug=t_slug,
                                               category__slug=c_slug)
        return context


class NewThread(LoginRequiredMixin, CreateView):
    form_class = ThreadForm
    template_name = 'forum/new_thread.html'

    def get_context_data(self, **kwargs):
        "Pass Category from url to context"
        context = super(NewThread, self).get_context_data(**kwargs)
        context['category'] = Category.objects.get(
            slug=self.kwargs['category_slug'])
        return context

    def form_valid(self, form):
        "Handle thread and 1st post creation in the db"
        # Create the thread
        t = Thread.objects.create(
            title=self.request.POST['title'],
            author=self.request.user,
            category=Category.objects.get(slug=self.kwargs['category_slug']))
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

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super(NewPost, self).get_context_data(**kwargs)
        context['category'] = self.kwargs['category_slug']
        context['thread'] = self.kwargs['thread_slug']
        return context

    def form_valid(self, form):
        """ Handle post creation in the db"""
        c_slug = self.kwargs['category_slug']
        t_slug = self.kwargs['thread_slug']
        t = Thread.objects.get(slug=t_slug,
                               category__slug=c_slug)
        form.instance.thread = t
        form.instance.author = self.request.user
        form.instance.save()
        t.modified, self.post_pk = form.instance.created, form.instance.pk
        t.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return (reverse_lazy('forum:thread', kwargs=self.kwargs)
                + '#' + str(self.post_pk))


class QuotePost(NewPost):

    def get_initial(self):
        "Pass quoted post content as initial data for form"
        initial = super(QuotePost, self).get_initial()
        p = Post.objects.get(pk=self.kwargs['pk'])
        text = "[quote][b]{:s} a dit :[/b]\n{:s}[/quote]".format(
            p.author.username, p.content_plain)
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
        # Save the post
        form.instance.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        pk = str(self.kwargs.pop('pk'))
        self.kwargs['thread_slug'] = self.t
        return (reverse_lazy('forum:thread', kwargs=self.kwargs)
                + '#' + pk)
