from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView, CreateView, UpdateView,\
    DetailView
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.contrib import messages

import re
from datetime import datetime
from braces.views import LoginRequiredMixin

from .models import Category, Thread, Post, Preview, PollQuestion
from .forms import ThreadForm, PostForm, PollThreadForm, QuestionForm, \
    ChoicesFormSet, FormSetHelper
from .util import get_query
from user.models import CategoryTimeStamp, Bookmark


THREADVIEW_PAGINATE_BY = 30
POSTVIEW_PAGINATE_BY = 30


### Helpers ###
def get_post_page(thread, post):
    """Return page number the post is on.
    
    Let's build a paginator object and check if our post is on the expected
    page. If not (because of PostView.paginate_orphans), return next page.
    """
    queryset = Post.objects.filter(thread=thread)
    page_size = PostView.paginate_by
    paginator = Paginator(
        queryset, page_size, orphans=PostView.paginate_orphans,
        allow_empty_first_page=False)
    index = queryset.filter(pk__lt=post.pk).count()
    page_number = max(index // PostView.paginate_by, 1)
    page = paginator.page(page_number)
    if post in page.object_list:
        return page_number
    else:
        return page_number + 1


def update_category_timestamp(category, user):
    """Update CategoryTimeStamp so category doesn't display unread status"""
    timestamp, created = CategoryTimeStamp.objects.get_or_create(
        category=category, user=user)
    timestamp.save()


### Mixins ###
class CategoryReadMixin(object):
    """Mark category as read."""

    def render_to_response(self, context, **response_kwargs):
        CategoryTimeStamp.objects.update_or_create(
            user=self.request.user, category=self.category)
        return super().render_to_response(context, **response_kwargs)


class ThreadStatusMixin(object):
    """Populate thread status."""

    def get_context_data(self, **kwargs):
           
        def get_bookmarked_post(thread, bookmark):
            """Return latest read post and page from bookmark timestamp."""
            post = Post.objects\
                       .filter(thread=thread, created__gt=bookmark)\
                       .only('id', 'pk').first()
            if post:
                page = get_post_page(thread, post)
                return post, page
            else:
                return post, None

        user_id = self.request.user.id
        context = super().get_context_data(**kwargs)
        bookmarks = self.request.user.cached_bookmarks
        for t in context['object_list']:
            # get thread's bookmark and check if there are unread items
            b = bookmarks.get(t.pk, None)
            if b:
                unread_items = t.modified > b
            else:
                unread_items = (True if t.modified > 
                                self.request.user.resetDateTime else False)
            key = make_template_fragment_key('thread_status', [t.pk,
                self.request.user.pk, self.request.user.resetDateTime])
            cached = cache.get('read_status/{}/{}'.format(user_id, t.id)) 
            # check whether additional calculation is needed
            tmp = cache.has_key(key)
            if cache.has_key(key) and cached == 'unread' and unread_items:
                continue
            elif cache.has_key(key) and cached == 'read' and not unread_items:
                continue
            else:
                cache.delete(key)
            # add bookmark and page to thread object
            if b:
                t.bookmark, t.page = get_bookmarked_post(t, b)
            else:
                t.bookmark, t.page = True, 1
            # now check if user is a contributor in this thread
            is_contributor = (True if
                t.contributors.filter(id=user_id) else False)
            # now we've got all the data we needed, let's choose the correct
            # status icon and behaviour
            if unread_items:
                status = 'unread_contributor' if is_contributor else 'unread'
                cache.set('read_status/{}/{}'.format(user_id, t.id), 'unread', None)
            else:
                status = 'read_contributor' if is_contributor else 'read'
                t.bookmark = None
                cache.set('read_status/{}/{}'.format(user_id, t.id), 'read', None)
            t.status = 'img/{}.png'.format(status)
        return context


class PreviewPostMixin(object):
    """Handle post preview by creating a temporary object."""

    def post(self, request, *args, **kwargs):
        if "preview" in request.POST:
            return self.get_preview(request.POST['content_plain'])
        else:
            return super().post(request, *args, **kwargs)

    @staticmethod
    def get_preview(content):
        """Redirect to PreviewView."""
        p = Preview.objects.create(content_plain=content)
        return HttpResponseRedirect(
            reverse('forum:preview', kwargs={'pk': p.pk}))


### Main Forum Views ###
class CategoryView(LoginRequiredMixin, ListView):
    """View of the different categories."""
    model = Category
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        timestamps = CategoryTimeStamp.objects.filter(user=self.request.user)
        for c in context['categories']:
            # to avoid non existent timestamps
            timestamp, created = timestamps.get_or_create(
                category=c, user=self.request.user)
            # compute and add read/unread status to category object
            status = ('unread' if c.threads.latest().modified >
                      timestamp.timestamp else 'read')
            c.status = 'img/{}.png'.format(status)
        return context


class ThreadView(LoginRequiredMixin, ThreadStatusMixin, CategoryReadMixin,
                 ListView):
    paginate_by = THREADVIEW_PAGINATE_BY
    paginate_orphans = 2

    def get(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category, slug=kwargs['category_slug'])
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Get the threads to be displayed."""
        return self.category.threads.filter(visible=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class PostView(LoginRequiredMixin, CategoryReadMixin, ListView):
    paginate_by = POSTVIEW_PAGINATE_BY
    paginate_orphans = 2

    def get(self, request, *args, **kwargs):
        self.thread = get_object_or_404(
            Thread,
            slug=kwargs['thread_slug'],
            category__slug=kwargs['category_slug'])
        self.category = self.thread.category
        if not self.thread.visible:  # 403 if the thread has been removed
            raise PermissionDenied
        # Decide whether Post.viewCount should be incremented
        bookmarks = request.user.cached_bookmarks
        b = bookmarks.get(self.thread.pk, None)
        # If b > t.modified, user has visited this thread since last post
        # (so no incr), if None, post has never been visited (so incr)
        increment = self.thread.modified > b if b else True
        if increment:
            self.thread.viewCount += 1  # Increment views
            self.thread.save()
        # Update thread's bookmark
        Bookmark.objects.update_or_create(user=request.user,
            thread=self.thread)
        cache.set('read_status/{}/{}'.format(self.request.user.id,
            self.thread.id), 'read', None)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Get the posts to be displayed."""
        return self.thread.posts.all()

    def get_context_data(self, **kwargs):
        """Add context data for template."""
        context = super().get_context_data(**kwargs)
        context['thread'] = self.thread
        return context


class PostDetailView(DetailView):
    "Displays a single post"
    model = Post


### Thread and Post creation and edit ###
class NewThread(LoginRequiredMixin, PreviewPostMixin, CategoryReadMixin,
                CreateView):
    form_class = ThreadForm
    template_name = 'forum/thread_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category, slug=kwargs['category_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Pass Category from url to context"""
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'category_slug': self.kwargs['category_slug']})
        return kwargs

    def form_valid(self, form):
        """Handle thread and 1st post creation in the db"""
        # Create the thread
        thread = Thread.objects.create(
            title=form.cleaned_data['title'],
            icon=form.cleaned_data['icon'],
            author=self.request.user,
            category=self.category,
            personal=form.cleaned_data['personal'])
        # Complete the post and save it
        form.instance.thread = thread
        form.instance.author = self.request.user
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('forum:category', kwargs=self.kwargs)


class NewPost(LoginRequiredMixin, PreviewPostMixin, CategoryReadMixin,
              CreateView):
    form_class = PostForm
    template_name = 'forum/post_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.thread = get_object_or_404(
            Thread,
            slug=kwargs['thread_slug'],
            category__slug=kwargs['category_slug'])
        self.category = self.thread.category
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['thread'] = self.thread
        context['history'] = Post.objects.filter(
            thread=self.thread).order_by('-pk')[:10]
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'category_slug': self.kwargs['category_slug'],
                       'thread': self.thread,
                       'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        "Update remaining form fields"
        form.instance.thread = self.thread
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return (reverse_lazy('forum:thread', kwargs=self.kwargs)
                + '?page=last#' + str(self.object.pk))


class QuotePost(NewPost):
    """Quote the content of another post"""

    def dispatch(self, request, *args, **kwargs):
        self.p = get_object_or_404(Post, pk=kwargs['pk'])
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
    template_name_suffix = '_edit'

    def dispatch(self, request, *args, **kwargs):
        "Get the right post and thread"
        self.p = get_object_or_404(Post, pk=kwargs['pk'])
        if self.p.author != request.user:
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
        t = get_object_or_404(Thread, pk=kwargs['pk'])
        if t.author != request.user or not t.personal:
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
    category = get_object_or_404(Category, slug=category_slug)
    thread_form = PollThreadForm(prefix="thread")
    question_form = QuestionForm(prefix="question")
    choices_formset = ChoicesFormSet(instance=PollQuestion())
    formset_helper = FormSetHelper()

    if request.method == 'POST':
        if "preview" in request.POST:
            return PreviewPostMixin.get_preview(
                request.POST['thread-content_plain'])
        else:
            thread_form = PollThreadForm(request.POST, prefix="thread")
            question_form = QuestionForm(request.POST, prefix="question")
            choices_formset = ChoicesFormSet(request.POST)
            if (thread_form.is_valid() and question_form.is_valid()
                    and choices_formset.is_valid()):
                # Create the thread
                thread = Thread.objects.create(
                    title=thread_form.cleaned_data['title'],
                    icon=thread_form.cleaned_data['icon'],
                    author=request.user,
                    category=category,
                    personal=thread_form.cleaned_data['personal'])
                # Complete the post and save it
                thread_form.instance.thread = thread
                thread_form.instance.author = request.user
                p = thread_form.save()
                # Complete the poll and save it
                question_form.instance.thread = thread
                question = question_form.save()
                choices_formset = ChoicesFormSet(request.POST,
                                                 instance=question)
                if choices_formset.is_valid():
                    choices_formset.save()
                    # Mark category as read
                    CategoryTimeStamp.objects.update_or_create(
                        category=category, user=request.user)
                    return HttpResponseRedirect(reverse(
                        'forum:category',
                        kwargs={'category_slug': category_slug}))

    return render(request, 'forum/poll_form.html', {
        'question_form': question_form,
        'thread_form': thread_form,
        'choices_formset': choices_formset,
        'formset_helper': formset_helper,
        'category_slug': category_slug,
        'category': category,
    })


@login_required
def VotePoll(request, category_slug, thread_slug):
    thread = get_object_or_404(Thread,
                               slug=thread_slug,
                               category__slug=category_slug)
    question = thread.question

    if request.method == 'POST':
        choice_text = request.POST.get('choice_text')
        if request.user not in question.voters.all() and choice_text:
            choice = question.choices.get(choice_text=choice_text)
            choice.votes += 1
            question.voters.add(request.user)
            choice.save()
            question.save()
        elif not choice_text:
            messages.error(request, "Aucun choix sélectionné.")
        else:
            messages.error(request, "Vous avez déjà voté.")
        return HttpResponseRedirect(reverse(
            'forum:thread', kwargs={'category_slug': category_slug,
                                    'thread_slug': thread_slug}))


### Search View ###
class SearchView(LoginRequiredMixin, ThreadStatusMixin, ListView):
    paginate_by = 30
    paginate_orphans = 2
    template_name = 'forum/search_results.html'

    def get(self, request, *args, **kwargs):
        """Return an error message if the query was empty."""
        self.query = request.GET['q']
        if not self.query:
            messages.error(request, "Aucun terme précisé pour la recherche.")
            return HttpResponseRedirect(reverse('forum:top'))
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Handle search parameters & process search computation."""
        cls = Thread
        if re.findall(r'^user:', self.query):
            entry_query = get_query(self.query[5:], ['author__username'])
        elif re.findall(r'^post:', self.query):
            cls = Post
            entry_query = get_query(self.query[5:], ['content_plain'])
        else:
            entry_query = get_query(self.query, ['title'])
        results = cls.objects.filter(entry_query)
        if 'visible' in [field.name for field in cls._meta.fields]:
            results = results.filter(visible="True")
        self.results_count = results.count()
        if not self.results_count:
            messages.error(
                self.request,
                "Aucun résultat ne correspond à cette recherche.")
        else:
            messages.success(
                self.request,
                "{} résultat(s) trouvé(s).".format(self.results_count))
        return results

    def get_context_data(self, **kwargs):
        """Add context data for the template."""
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
