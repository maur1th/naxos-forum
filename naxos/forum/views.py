from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView, CreateView, UpdateView,\
    DetailView
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist

import re
import datetime
from braces.views import LoginRequiredMixin

from .models import Category, Thread, Post, Preview, PollQuestion
from .forms import ThreadForm, PostForm, PollThreadForm, QuestionForm, \
    ChoicesFormSet, FormSetHelper
from .util import get_query


### Helpers ###
def get_preview(content):
    "Redirect to post preview"
    p = Preview.objects.create(content_plain=content)
    return HttpResponseRedirect(reverse('forum:preview', kwargs={'pk': p.pk}))

class ThreadStatusMixin(object):
    "Populate thread status and readCaret where needed"

    def get_context_data(self, **kwargs):
           
        def get_post_page(post):
            return  post.position // PostView.paginate_by + 1

        context = super().get_context_data(**kwargs)
        user = self.request.user
        readCaret = cache.get("user/{}/readCaret".format(user.pk))
        if not readCaret:
            readCaret = user.postsReadCaret.all()
            cache.set("user/{}/readCaret".format(user.pk),
                  readCaret, None)
        for t in context['object_list']:
            contributors = cache.get("thread/{}/contributors".format(t.pk))
            if not contributors:  # caches thread's contributors
                contributors = t.contributors.all()
                cache.set("thread/{}/contributors".format(t.pk),
                  contributors, None)
            # Get latest_post from cache or create it
            latest_post = cache.get("thread/{}/latest_post".format(t.pk))
            if not latest_post:
                latest_post = t.latest_post
                cache.set("thread/{}/latest_post".format(t.pk),
                          latest_post, None)
            uptodate_caret = latest_post in readCaret
            if user in contributors and uptodate_caret:
                status = "added"
            elif user in contributors:
                status = "added+on"
                try:
                    t.readCaret = readCaret.get(thread=t)
                    t.readCaret.page = get_post_page(t.readCaret)
                except ObjectDoesNotExist:
                    t.readCaret = "not_visited"
            elif uptodate_caret:
                status = "off"
            else:
                status = "on"
                try:
                    t.readCaret = readCaret.get(thread=t)
                    t.readCaret.page = get_post_page(t.readCaret)
                except ObjectDoesNotExist:
                    t.readCaret = "not_visited"
            t.status = 'img/{}.png'.format(status)
        return context


class PreviewPostMixin(object):
    def post(self, request, *args, **kwargs):
        if "preview" in request.POST:
            return get_preview(request.POST['content_plain'])
        else:
            return super().post(request, *args, **kwargs)


### Main Forum Views ###
class TopView(LoginRequiredMixin, ListView):
    model = Category

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['readCaret'] = self.request.user.postsReadCaret.all()
        return context


class ThreadView(LoginRequiredMixin, ThreadStatusMixin, ListView):
    paginate_by = 30
    paginate_orphans = 2

    def get_queryset(self):
        "Return threads of the current category ordered by latest post"
        self.c = get_object_or_404(Category,
                                   slug=self.kwargs['category_slug'])
        return self.c.threads.select_related('author', 'question')\
                             .filter(visible=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.c
        return context


class PostView(LoginRequiredMixin, ListView):
    paginate_by = 5
    paginate_orphans = 2

    def dispatch(self, request, *args, **kwargs):
        c_slug = self.kwargs['category_slug']
        t_slug = self.kwargs['thread_slug']
        self.t = get_object_or_404(Thread, slug=t_slug, category__slug=c_slug)
        # 403 if the thread has been removed
        if not self.t.visible:
            raise PermissionDenied
        self.t.viewCount += 1  # Increment views
        self.t.save()
        # Handle user read caret
        p = self.t.latest_post
        try:
            caret = self.request.user.postsReadCaret.get(thread=self.t)
        except:
            caret = False
        if caret != p:
            self.request.user.postsReadCaret.remove(caret)
            self.request.user.postsReadCaret.add(p)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        "Return list of posts given thread and category slugs"
        return self.t.posts.all()

    def get_context_data(self, **kwargs):
        "Pass thread from url to context"
        context = super().get_context_data(**kwargs)
        context['thread'] = self.t
        return context


class PostDetailView(DetailView):
    "Displays a single post"
    model = Post


### Thread and Post creation and edit ###
class NewThread(LoginRequiredMixin, PreviewPostMixin, CreateView):
    form_class = ThreadForm
    template_name = 'forum/new_thread.html'

    def dispatch(self, request, *args, **kwargs):
        self.c = get_object_or_404(
            Category, slug=self.kwargs['category_slug'])
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
            category=self.c,
            personal=form.cleaned_data['personal'])
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
        self.t = get_object_or_404(
            Thread,
            slug=self.kwargs['thread_slug'],
            category__slug=self.kwargs['category_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super().get_context_data(**kwargs)
        context['category'] = self.t.category
        context['thread'] = self.t
        context['history'] = Post.objects.filter(
            thread=self.t).order_by('-pk')[:10]
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'category_slug': self.kwargs['category_slug'],
                       'thread': self.t})
        return kwargs

    def form_valid(self, form):
        "Handle post creation in the db"
        # Update category and thread
        self.t.category.postCount += 1
        self.t.category.save()
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
        self.p = get_object_or_404(Post, pk=self.kwargs['pk'])
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
        self.p = get_object_or_404(Post, pk=self.kwargs['pk'])
        if self.p.author != self.request.user:
            raise PermissionDenied
        self.t = self.p.thread
        self.c = self.t.category
        return super().dispatch(request, *args, **kwargs)

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
        # Edit thread title if indeed the first post
        if self.p == self.t.posts.first():
            self.t.title = form.cleaned_data['title']
            self.t.icon = form.cleaned_data['icon']
            self.t.save()
        form.instance.modified = datetime.datetime.now()
        return super().form_valid(form)

    def get_success_url(self):
        self.kwargs.pop('pk')  # remove useless pk
        self.kwargs['thread_slug'] = self.t.slug
        post_page = self.object.position//PostView.paginate_by + 1
        return (reverse_lazy('forum:thread', kwargs=self.kwargs)
                + '?page=' + str(post_page) + '#' + str(self.object.pk))


class DeleteThread(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        t = get_object_or_404(Thread, pk=self.kwargs['pk'])
        if t.author != self.request.user or not t.personal:
            raise PermissionDenied
        else:
            t.visible = False
            t.save()
            return HttpResponseRedirect(reverse('forum:category',
                kwargs={'category_slug': t.category}))


class PreviewView(LoginRequiredMixin, DetailView):
    model = Preview

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        self.object.delete()  # Now the object is loaded, delete it
        return self.render_to_response(context)


### Poll Views ###
@login_required
def NewPoll(request, category_slug):
    c = get_object_or_404(Category, slug=category_slug)
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
            choices_formset = ChoicesFormSet(request.POST)
            if (thread_form.is_valid() and question_form.is_valid()
                    and choices_formset.is_valid()):
                # Create the thread
                t = Thread.objects.create(
                    title=thread_form.cleaned_data['title'],
                    icon=thread_form.cleaned_data['icon'],
                    author=request.user,
                    category=c,
                    personal=thread_form.cleaned_data['personal'])
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
    thread = get_object_or_404(Thread,
                               slug=thread_slug,
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


### Search View ###
class SearchView(LoginRequiredMixin, ThreadStatusMixin, ListView):
    paginate_by = 30
    paginate_orphans = 2
    template_name = 'forum/search_results.html'

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.query = self.request.GET['q']
        cls = Thread
        if not self.query:  # An empty string was submitted
            return
        elif re.findall(r'^user:', self.query):
            entry_query = get_query(self.query[5:], ['author__username'])
        elif re.findall(r'^post:', self.query):
            cls = Post
            entry_query = get_query(self.query[5:], ['content_plain'])
        else:
            entry_query = get_query(self.query, ['title'])
        return cls.objects.filter(entry_query)

    def get_context_data(self, **kwargs):
        model = self.object_list.model._meta.model_name
        if model == 'thread':
            context = super().get_context_data(**kwargs)
        else:
            context = ListView.get_context_data(self, **kwargs)
        context['model'] = model
        context['query'] = self.query
        context['query_url'] = 'q=' + self.query + '&amp;'
        return context
