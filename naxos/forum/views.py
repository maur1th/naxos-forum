from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView, CreateView, UpdateView,\
    DetailView
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist

import re
from datetime import datetime
from braces.views import LoginRequiredMixin

from .models import Category, Thread, Post, Preview, PollQuestion
from .forms import ThreadForm, PostForm, PollThreadForm, QuestionForm, \
    ChoicesFormSet, FormSetHelper
from .util import get_query
from user.models import Bookmark


### Helpers ###
def get_preview(content):
    "Redirect to post preview"
    p = Preview.objects.create(content_plain=content)
    return HttpResponseRedirect(reverse('forum:preview', kwargs={'pk': p.pk}))


def get_post_page(thread, post):
    num_posts = thread.posts.count()
    if num_posts % PostView.paginate_by > PostView.paginate_orphans:
        return post.position // PostView.paginate_by + 1
    else:
        if num_posts - post.position <= PostView.paginate_orphans:
            return post.position // PostView.paginate_by
        else:
            return post.position // PostView.paginate_by + 1


### Mixins ###
class ThreadStatusMixin(object):
    "Populate thread status and readCaret where needed"

    def get_context_data(self, **kwargs):
           
        def get_bookmarked_post(thread, bookmark):
            post = Post.objects.filter(
                        thread=thread, created__gt=bookmark).first()
            if post:
                page = get_post_page(thread, post)
                return post, page
            else:
                return post, None

        context = super().get_context_data(**kwargs)
        bookmarks = self.request.user.cached_bookmarks
        for t in context['object_list']:
            # get thread status cache key for this thread / user
            key = make_template_fragment_key(
                'thread_status',
                [t.pk, self.request.user.pk, self.request.user.resetDateTime])
            # get thread's bookmark and check if there are unread items
            b = bookmarks.get(t.pk, None)
            if b:
                unread_items = t.modified > b
                t.bookmark, t.page = get_bookmarked_post(t, b)
            else:
                # in case there is no bookmark for this thread
                unread_items = (True if t.modified > 
                                self.request.user.resetDateTime else False)
            # check whether additional calculation is needed
            if unread_items:
                cache.delete(key)
            elif not cache.has_key(key):
                pass
            else:  # no unread items & cache exists? then skip the rest!
                continue
            # now check if user is a contributor in this thread
            is_contributor = Thread.objects.filter(
                pk=t.pk, contributors=self.request.user).exists()
            # now we've got all the data we needed, let's choose the correct
            # status icon and behaviour
            if unread_items and is_contributor:
                status = "unread_contributor"
                if not hasattr(t, 'bookmark'):
                    t.bookmark, t.page = t.posts.first(), 1
            elif unread_items:
                status = "unread"
                if not hasattr(t, 'bookmark'):
                    t.bookmark, t.page = t.posts.first(), 1
            elif is_contributor:
                status, t.bookmark = "read_contributor", None
            else:
                status, t.bookmark = "read", None
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
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for c in context['categories']:
            try:
                latest_bookmark = Bookmark.objects\
                    .filter(user=self.request.user, thread__category=c)\
                    .values_list('timestamp').latest()[0]
            except ObjectDoesNotExist:
                latest_bookmark = self.request.user.resetDateTime
            c.latest_thread = c.threads.latest()
            status = ('unread' if c.latest_thread.modified >
                      latest_bookmark else 'read')
            c.status = 'img/{}.png'.format(status)
        return context


class ThreadView(LoginRequiredMixin, ThreadStatusMixin, ListView):
    paginate_by = 30
    paginate_orphans = 2

    def get_queryset(self):
        "Return threads of the current category ordered by latest post"
        self.c = get_object_or_404(Category,
                                   slug=self.kwargs['category_slug'])
        return self.c.threads.filter(visible=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.c
        return context


class PostView(LoginRequiredMixin, ListView):
    paginate_by = 30
    paginate_orphans = 2

    def dispatch(self, request, *args, **kwargs):
        c_slug = self.kwargs['category_slug']
        t_slug = self.kwargs['thread_slug']
        self.t = get_object_or_404(Thread, slug=t_slug, category__slug=c_slug)
        if not self.t.visible:  # 403 if the thread has been removed
            raise PermissionDenied
        if not request.user.is_authenticated():  # redirect to login page
            return super().dispatch(request, *args, **kwargs)
        # Decide whether Post.viewCount should be incremented
        bookmarks = self.request.user.cached_bookmarks
        b = bookmarks.get(self.t.pk, None)
        # If b > t.modified, user has visited this thread since last post
        # (so no incr), if None, post has never been visited (so incr)
        increment = self.t.modified > b if b else True
        if increment:
            self.t.viewCount += 1  # Increment views
            self.t.save()
        # Now update or create Bookmark's timestamp (see user.models)
        Bookmark.objects.update_or_create(user=request.user,
                                          thread=self.t)
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
    template_name = 'forum/thread_form.html'

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
        form.instance.author = self.request.user
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('forum:category', kwargs=self.kwargs)


class NewPost(LoginRequiredMixin, PreviewPostMixin, CreateView):
    form_class = PostForm
    template_name = 'forum/post_form.html'

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
                       'thread': self.t,
                       'user':self.request.user})
        return kwargs

    def form_valid(self, form):
        "Update remaining form fields"
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
        initial_text = re.sub(r'\[quote\][\S|\s]+\[/quote\]\r{0,1}\n{0,1}',
                              '',
                              self.p.content_plain)
        text = "[quote][b]{:s} a dit :[/b]\n{:s}[/quote]".format(
            self.p.author.username, initial_text)
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
        form.instance.modified = datetime.now()
        return super().form_valid(form)

    def get_success_url(self):
        self.kwargs.pop('pk')  # remove useless pk
        self.kwargs['thread_slug'] = self.t.slug
        post_page = get_post_page(self.t, self.p)
        return (reverse_lazy('forum:thread', kwargs=self.kwargs)
                + '?page=' + str(post_page) + '#' + str(self.object.pk))


class ResetBookmarks(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if kwargs['pk'] != str(request.user.pk):
            raise PermissionDenied
        else:
            # update all bookmark timestamps to now
            Bookmark.objects.filter(user=request.user)\
                .update(timestamp=datetime.now())
            # record resetDateTime on user
            request.user.resetDateTime = datetime.now()
            request.user.save()
            # delete cached bookmarks & force re-cache
            cache.delete('bookmark/{}'.format(request.user.pk))
            request.user.cached_bookmarks
        return HttpResponseRedirect(reverse('forum:top'))


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

    return render(request, 'forum/poll_form.html', {
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
        # Additional search options disabled since they make the server 500
        # for apparently no other reason than load
        # elif re.findall(r'^user:', self.query):
        #     entry_query = get_query(self.query[5:], ['author__username'])
        # elif re.findall(r'^post:', self.query):
        #     cls = Post
        #     entry_query = get_query(self.query[5:], ['content_plain'])
        else:
            entry_query = get_query(self.query, ['title'])
        results = cls.objects.filter(entry_query)
        if 'visible' in [field.name for field in cls._meta.fields]:
            results = results.filter(visible="True")
        self.results_count = results.count()
        return results

    def get_context_data(self, **kwargs):
        model = self.object_list.model._meta.model_name
        if model == 'thread':
            context = super().get_context_data(**kwargs)
        else:
            context = ListView.get_context_data(self, **kwargs)
        context['model'] = model
        context['query'] = self.query
        context['results_count'] = self.results_count
        context['query_url'] = 'q=' + self.query + '&amp;'
        return context
