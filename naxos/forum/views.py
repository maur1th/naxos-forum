from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

import datetime
from braces.views import LoginRequiredMixin

from .models import Category, Thread, Post, Preview, PollQuestion
from .forms import ThreadForm, PostForm, PollThreadForm, QuestionForm, \
    ChoicesFormSet, FormSetHelper


### Helpers ###
def get_preview(author, content):
    "Redirects to a post preview."
    p = Preview.objects.create(author=author, content_plain=content)
    return HttpResponseRedirect(reverse('forum:preview', kwargs={'pk': p.pk}))


class PreviewPostMixin(object):
    def post(self, request, *args, **kwargs):
        if "preview" in request.POST:
            return get_preview(self.request.user,
                               request.POST['content_plain'])
        else:
            return super().post(request, *args, **kwargs)


### Main Forum Views ###
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
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        "Return threads of the current category ordered by latest post"
        return self.c.threads.all()

    def get_context_data(self, **kwargs):
        "Pass category from url to context"
        context = super().get_context_data(**kwargs)
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
        self.t.viewCount += 1  # Increment views
        # Handle user read caret
        p = self.t.posts.latest()
        try:
            caret = self.request.user.postsReadCaret.get(thread=self.t)
        except:
            caret = False
        if caret != p:
            self.request.user.postsReadCaret.remove(caret)
            self.request.user.postsReadCaret.add(p)
        self.t.save()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        "Return list of posts given thread and category slugs"
        return self.t.posts.all()

    def get_context_data(self, **kwargs):
        "Pass thread from url to context"
        context = super().get_context_data(**kwargs)
        context['thread'] = self.t
        return context


class PreviewView(DetailView):
    model = Preview

    def render_to_response(self, context, **response_kwargs):
        if self.request.user != self.object.author:
            return HttpResponseForbidden()
        return super().render_to_response(context, **response_kwargs)


### Thread and Post creation and edit ###
class NewThread(LoginRequiredMixin, PreviewPostMixin, CreateView):
    form_class = ThreadForm
    template_name = 'forum/new_thread.html'

    def dispatch(self, request, *args, **kwargs):
        self.c = Category.objects.get(slug=self.kwargs['category_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        "Pass Category from url to context"
        context = super().get_context_data(**kwargs)
        context['category'] = self.c
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'category_slug': self.kwargs['category_slug']})
        return kwargs

    def form_valid(self, form):
        "Handle thread and 1st post creation in the db"
        # Create the thread
        t = Thread.objects.create(
            title=self.request.POST['title'],
            author=self.request.user,
            category=self.c)
        # Complete the post and save it
        form.instance.thread = t
        form.instance.thread.category.postCount += 1  # Increment category
        form.instance.thread.category.save()          # post counter
        form.instance.author = self.request.user
        p = form.save()
        self.request.user.postsReadCaret.add(p)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('forum:category', kwargs=self.kwargs)


class NewPost(LoginRequiredMixin, PreviewPostMixin, CreateView):
    form_class = PostForm
    template_name = 'forum/new_post.html'

    def dispatch(self, request, *args, **kwargs):
        self.t = Thread.objects.get(
            slug=self.kwargs['thread_slug'],
            category__slug=self.kwargs['category_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super().get_context_data(**kwargs)
        context['category'] = self.t.category
        context['thread'] = self.t
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'category_slug': self.kwargs['category_slug'],
                       'thread': self.t})
        return kwargs

    def form_valid(self, form):
        "Handle post creation in the db"
        # Update parent category and thread
        self.t.modified = datetime.datetime.now()
        self.t.category.postCount += 1
        self.t.category.save()
        self.t.save()
        # Merge with last thread post if same author
        p = self.t.posts.latest()  # Get last post
        if p.author == self.request.user:
            # Update form accordingly
            form.instance.content_plain = p.content_plain + "\n\n{:s}".format(
                form.instance.content_plain)
            form.instance.created = p.created
            form.instance.modified = datetime.datetime.now()
            # Delete last post
            p.delete()
        # Update remaining form fields
        form.instance.thread = self.t
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return (reverse_lazy('forum:thread', kwargs=self.kwargs)
                + '#' + str(self.object.pk))


class QuotePost(NewPost):
    """Quote the content of another post"""

    def dispatch(self, request, *args, **kwargs):
        self.p = Post.objects.get(pk=self.kwargs['pk'])
        self.t = self.p.thread
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        "Pass quoted post content as initial data for form"
        initial = super().get_initial()
        text = "[quote][b]{:s} a dit :[/b]\n{:s}[/quote]".format(
            self.p.author.username, self.p.content_plain)
        initial['content_plain'] = text
        return initial


class EditPost(LoginRequiredMixin, PreviewPostMixin, UpdateView):
    form_class = ThreadForm
    model = Post
    template_name = 'forum/edit.html'

    def dispatch(self, request, *args, **kwargs):
        # Get the right post and thread
        self.p = Post.objects.get(pk=self.kwargs['pk'])
        self.t = self.p.thread
        self.c = self.t.category
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        "Pass thread title as initial data for form"
        initial = super().get_initial()
        initial['title'] = self.t.title
        return initial

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super().get_context_data(**kwargs)
        context['category'] = self.c
        context['thread'] = self.t
        context['post'] = self.p
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'category_slug': self.kwargs['category_slug'],
                       'thread': self.t,
                       'post': self.p})
        return kwargs

    def form_valid(self, form):
        "Handle thread and 1st post creation in the db"
        modified = False  # Handle modified datetime tag update
        # Edit thread title if indeed the first post
        if (self.p == self.t.posts.first()
                and self.request.POST['title'] != self.t.title):
            self.t.title = self.request.POST['title']
            modified = True
        self.t.save()
        if form.instance.content_plain != self.p.content_plain:
            modified = True
        if modified:
            form.instance.modified = datetime.datetime.now()
        # Save the post
        form.instance.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        pk = str(self.kwargs.pop('pk'))
        self.kwargs['thread_slug'] = self.t.slug
        return (reverse_lazy('forum:thread', kwargs=self.kwargs)
                + '#' + pk)


### Poll Views ###
@login_required
def NewPoll(request, category_slug):
    c = Category.objects.get(slug=category_slug)
    thread_form = PollThreadForm(prefix="thread")
    question_form = QuestionForm(prefix="question")
    choices_formset = ChoicesFormSet(instance=PollQuestion())
    formset_helper = FormSetHelper()

    if request.method == 'POST':
        if "preview" in request.POST:
            return get_preview(request.user,
                               request.POST['thread-content_plain'])
        else:
            thread_form = PollThreadForm(request.POST, prefix="thread")
            question_form = QuestionForm(request.POST, prefix="question")
            if thread_form.is_valid() and question_form.is_valid():
                # Create the thread
                t = Thread.objects.create(
                    title=request.POST['thread-title'],
                    author=request.user,
                    category=c)
                # Complete the post and save it
                thread_form.instance.thread = t
                thread_form.instance.author = request.user
                p = thread_form.save()
                request.user.postsReadCaret.add(p)
                # Complete the poll and save it
                question_form.instance.thread = t
                question = question_form.save()
                choices_formset = ChoicesFormSet(request.POST,
                                                 instance=question)
                if choices_formset.is_valid():
                    choices_formset.save()
                    return HttpResponseRedirect(reverse(
                        'forum:category',
                        kwargs={'category_slug': category_slug}))

    return render(request, 'forum/new_poll.html', {
        'question_form': question_form,
        'thread_form': thread_form,
        'choices_formset': choices_formset,
        'formset_helper': formset_helper,
        'category_slug': category_slug,
        'category': c,
    })


@login_required
def VotePoll(request, category_slug, thread_slug):
    thread = Thread.objects.get(slug=thread_slug,
                                category__slug=category_slug)
    question = thread.question

    if request.method == 'POST':
        if request.user not in question.voters.all():
            choice = question.choices.get(
                choice_text=request.POST['choice_text'])
            choice.votes += 1
            question.voters.add(request.user)
            choice.save()
            question.save()
        return HttpResponseRedirect(reverse(
            'forum:thread', kwargs={'category_slug': category_slug,
                                    'thread_slug': thread_slug}))
