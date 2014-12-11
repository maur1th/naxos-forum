from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response
from django.template import RequestContext

import re
import datetime
from braces.views import LoginRequiredMixin

from .models import Category, Thread, Post, Preview, PollQuestion, \
    ThreadCession
from .forms import ThreadForm, PostForm, PollThreadForm, QuestionForm, \
    ChoicesFormSet, FormSetHelper
from .util import get_query

MERGEPOST_INTERVAL = 300


### Search stuff ###
@login_required
def search(request):
    query_string = ''
    found_entries = None
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        if re.findall(r'^user:', query_string):
            entry_query = get_query(query_string[5:], ['author__username'])    
        else:
            entry_query = get_query(query_string, ['title',])
        print(entry_query)
        found_entries = Thread.objects.filter(entry_query)\
                                      .order_by("-isSticky", "-modified",
                                                "pk")

    return render_to_response('forum/search_results.html',
                              {'query_string': query_string,
                               'found_entries': found_entries},
                              context_instance=RequestContext(request))


### Helpers ###
def get_preview(content):
    "Redirect to post preview"
    p = Preview.objects.create(content_plain=content)
    return HttpResponseRedirect(reverse('forum:preview', kwargs={'pk': p.pk}))


class PreviewPostMixin(object):
    def post(self, request, *args, **kwargs):
        if "preview" in request.POST:
            return get_preview(request.POST['content_plain'])
        else:
            return super().post(request, *args, **kwargs)


### Main Forum Views ###
class TopView(LoginRequiredMixin, ListView):
    model = Category


class ThreadView(LoginRequiredMixin, ListView):
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
        context['post_pagination'] = PostView.paginate_by
        return context


class PostView(LoginRequiredMixin, ListView):
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
            title=form.cleaned_data['title'],
            icon=form.cleaned_data['icon'],
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
        interval = datetime.datetime.now() - p.created
        if (p.author == self.request.user
                and interval.seconds < MERGEPOST_INTERVAL):
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
                + '?page=last#' + str(self.object.pk))


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
        "Get the right post and thread"
        self.p = Post.objects.get(pk=self.kwargs['pk'])
        if self.p.author != self.request.user:
            return HttpResponseForbidden()
        self.t = self.p.thread
        self.c = self.t.category
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if "cede" in request.POST:
            ThreadCession.objects.get_or_create(thread=self.t)
            return HttpResponseRedirect(
                reverse('forum:cession',
                        kwargs={'category_slug': self.c.slug,
                                'thread_slug': self.t.slug}))
        else:
            return super().post(request, *args, **kwargs)

    def get_initial(self):
        "Pass initial data to form"
        initial = super().get_initial()
        initial['title'] = self.t.title
        initial['icon'] = self.t.icon[4:][:-4]
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
                and (form.cleaned_data['title'] != self.t.title
                     or form.cleaned_data['icon'] != self.t.icon)):
            self.t.title = form.cleaned_data['title']
            self.t.icon = form.cleaned_data['icon']
            modified = True
            self.t.save()
        if form.cleaned_data['content_plain'] != self.p.content_plain:
            modified = True
        if modified:
            form.instance.modified = datetime.datetime.now()
        return super().form_valid(form)

    def get_success_url(self):
        self.kwargs.pop('pk')  # remove useless pk
        self.kwargs['thread_slug'] = self.t.slug
        post_page = self.object.position//PostView.paginate_by + 1
        return (reverse_lazy('forum:thread', kwargs=self.kwargs)
                + '?page=' + str(post_page) + '#' + str(self.object.pk))


class PreviewView(LoginRequiredMixin, DetailView):
    model = Preview

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        self.object.delete()  # Now the object is loaded, delete it
        return self.render_to_response(context)


class ThreadCessionView(LoginRequiredMixin, DetailView):
    
    def dispatch(self, request, *args, **kwargs):
        self.t = Thread.objects.get(
                    slug=self.kwargs['thread_slug'],
                    category__slug=self.kwargs['category_slug'])
        if self.t.author != self.request.user:
            return HttpResponseForbidden()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return ThreadCession.objects.get(thread=self.t)


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
            return get_preview(request.POST['thread-content_plain'])
        else:
            thread_form = PollThreadForm(request.POST, prefix="thread")
            question_form = QuestionForm(request.POST, prefix="question")
            if thread_form.is_valid() and question_form.is_valid():
                # Create the thread
                t = Thread.objects.create(
                    title=thread_form.cleaned_data['title'],
                    icon=thread_form.cleaned_data['icon'],
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
