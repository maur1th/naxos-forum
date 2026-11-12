from django.shortcuts import render, get_object_or_404
from django.views.generic import View, ListView, CreateView, UpdateView,\
    DetailView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db import transaction
from django.db.models import Count, F, Min, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce, Lower
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

import math
import re
from urllib.parse import urlencode

from .models import BudgetRecord, Category, Thread, Post, Preview, PollQuestion, PollChoice, PollVote, UserMentions
from .forms import PostForm, PollThreadForm, QuestionForm, \
    ChoicesFormSet, FormSetHelper
from .util import get_query
from utils.renderer import UserReferences
from user.models import Bookmark, CategoryTimeStamp, ForumUser, \
    MENTION_USERS_KEY

THREADVIEW_PAGINATE_BY = 30
POSTVIEW_PAGINATE_BY = 30


# Helpers #
def page_for_index(index, count):
    """
    Return the PostView page holding the post at 0-based `index` in a thread
    of `count` posts: the last page also takes up to `paginate_orphans`
    trailing posts, as Django's Paginator does.
    """
    per_page = PostView.paginate_by
    num_pages = max(1, math.ceil(
        max(1, count - PostView.paginate_orphans) / per_page))
    return min(index // per_page + 1, num_pages)


def get_post_pages(post_ids):
    """Return {post pk: page number} for these posts, in one query."""
    if not post_ids:
        return {}

    def count_posts(**filters):
        return Coalesce(Subquery(
            Post.objects.filter(thread=OuterRef('thread'), **filters)
            .order_by().values('thread').annotate(n=Count('pk'))
            .values('n')), 0)

    rows = Post.objects.filter(pk__in=post_ids).annotate(
        index=count_posts(pk__lt=OuterRef('pk')),
        total=count_posts(),
    ).values_list('pk', 'index', 'total')
    return {pk: page_for_index(index, total) for pk, index, total in rows}


def add_post_pages(posts):
    """Set `page` on each post."""
    posts = list(posts)
    pages = get_post_pages([p.pk for p in posts])
    for post in posts:
        post.page = pages[post.pk]


def get_post_page(post):
    """Return page number the post is on."""
    return get_post_pages([post.pk])[post.pk]


def get_all_users():
    """Usernames of active members, for the mention autocomplete."""
    users = cache.get(MENTION_USERS_KEY)
    if users is None:
        users = [f"@{username}" for username in ForumUser.objects
                 .filter(is_active=True).order_by(Lower('username'))
                 .values_list('username', flat=True)]
        cache.set(MENTION_USERS_KEY, users, None)
    return users


def mark_category_read(user, category):
    """Record the user's visit to the category (one query when it exists)."""
    if not CategoryTimeStamp.objects.filter(user=user, category=category)\
            .update(timestamp=timezone.now()):
        CategoryTimeStamp.objects.get_or_create(user=user, category=category)


# Mixins #
class CategoryReadMixin(object):
    """Mark category as read."""

    def render_to_response(self, context, **response_kwargs):
        mark_category_read(self.request.user, self.category)
        return super().render_to_response(context, **response_kwargs)


class ThreadStatusMixin(object):
    """Populate thread status."""

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        bookmarks = user.cached_bookmarks
        stale = []  # (thread, bookmark timestamp, has unread posts)
        for t in context['object_list']:
            # get thread's bookmark and check if there are unread items
            b = bookmarks.get(t.pk, None)
            if b:
                unread_items = t.modified > b
            else:
                unread_items = t.modified > user.resetDateTime
            key = make_template_fragment_key(
                'thread_status', [t.pk, user.pk, user.resetDateTime])
            cached = cache.get('read_status/{}/{}'.format(user.id, t.id))
            # check whether additional calculation is needed
            if key in cache and \
                    cached == ('unread' if unread_items else 'read'):
                continue
            cache.delete(key)
            stale.append((t, b, unread_items))
        if not stale:
            return context

        # Batch what the stale threads need: whether the user contributed,
        # and for unread bookmarked threads the first unread post and page.
        contributed = set(Thread.contributors.through.objects.filter(
            forumuser_id=user.id,
            thread_id__in=[t.pk for t, _, _ in stale],
        ).values_list('thread_id', flat=True))
        unread_since = Q()
        for t, b, unread_items in stale:
            if b and unread_items:
                unread_since |= Q(thread_id=t.pk, created__gt=b)
        first_unread = {}
        if unread_since:
            first_unread = dict(
                Post.objects.filter(unread_since).order_by()
                .values('thread_id').annotate(first=Min('pk'))
                .values_list('thread_id', 'first'))
        pages = get_post_pages(list(first_unread.values()))

        for t, b, unread_items in stale:
            is_contributor = t.pk in contributed
            # now we've got all the data we needed, let's choose the correct
            # status icon and behaviour
            if unread_items:
                if b:
                    post_id = first_unread.get(t.pk)
                    t.bookmark = Post(pk=post_id) if post_id else None
                    t.page = pages.get(post_id)
                else:
                    t.bookmark, t.page = True, 1
                status = 'unread_contributor' if is_contributor else 'unread'
                cache.set(
                    'read_status/{}/{}'.format(user.id, t.id), 'unread', None
                )
            else:
                status = 'read_contributor' if is_contributor else 'read'
                t.bookmark = None
                cache.set(
                    'read_status/{}/{}'.format(user.id, t.id), 'read', None
                )
            t.status = 'img/{}.png'.format(status)
        return context


class PreviewPostMixin(object):
    """Handle post preview by creating a temporary object."""

    def post(self, request, *args, **kwargs):
        if "preview" in request.POST:
            return self.get_preview(request.POST['content_plain'], request.user)
        else:
            return super().post(request, *args, **kwargs)

    @staticmethod
    def get_preview(content, user):
        """Redirect to PreviewView."""
        p = Preview.objects.create(content_plain=content, author=user)
        return HttpResponseRedirect(
            reverse('forum:preview', kwargs={'pk': p.pk}))


# Main Forum Views #
class CategoryView(LoginRequiredMixin, ListView):
    """View of the different categories."""
    model = Category
    context_object_name = 'categories'

    def get_queryset(self):
        latest = Thread.objects.filter(category=OuterRef('pk'), visible=True)\
            .order_by('-modified')
        return Category.objects.annotate(
            thread_count=Count('threads'),
            latest_thread_id=Subquery(latest.values('pk')[:1]),
        ).order_by('pk')  # Meta.ordering is ignored once aggregated

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['budget_total'] = BudgetRecord.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        context['budget_status'] = 'danger' if context['budget_total'] < 0 else 'success'
        user = self.request.user
        categories = context['categories']
        timestamps = dict(CategoryTimeStamp.objects.filter(user=user)
                          .values_list('category_id', 'timestamp'))
        # to avoid non existent timestamps
        now = timezone.now()
        missing = [c.pk for c in categories if c.pk not in timestamps]
        if missing:
            CategoryTimeStamp.objects.bulk_create(
                [CategoryTimeStamp(user=user, category_id=pk, timestamp=now)
                 for pk in missing],
                ignore_conflicts=True)
            timestamps.update(dict.fromkeys(missing, now))
        # latest visible thread of each category, with its latest post
        latest_post = Post.objects.filter(thread=OuterRef('pk'))\
            .order_by('-created')
        threads = Thread.objects.filter(
            pk__in=[c.latest_thread_id for c in categories
                    if c.latest_thread_id],
        ).annotate(latest_post_id=Subquery(latest_post.values('pk')[:1]))\
            .in_bulk()
        posts = Post.objects.select_related('author').in_bulk(
            [t.latest_post_id for t in threads.values() if t.latest_post_id])
        for c in categories:
            c.latest_thread = threads.get(c.latest_thread_id)
            if c.latest_thread:
                c.latest_thread.last_post = posts.get(
                    c.latest_thread.latest_post_id)
            # compute and add read/unread status to category object
            latest = c.latest_thread and c.latest_thread.modified
            c.status = 'img/{}.png'.format(
                "unread" if latest and latest > timestamps[c.pk]
                else "read")
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
        return self.category.threads.filter(visible=True)\
            .select_related('author', 'question')

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
            category__slug=kwargs['category_slug'],
            visible=True)
        self.category = self.thread.category
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
        Bookmark.objects.update_or_create(
            user=request.user, thread=self.thread)
        cache.set(
            'read_status/{}/{}'.format(self.request.user.id, self.thread.id),
            'read',
            None
        )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Get the posts to be displayed."""
        return self.thread.posts.all()

    def get_context_data(self, **kwargs):
        """Add context data for template."""
        context = super().get_context_data(**kwargs)
        context['thread'] = self.thread
        context['users'] = get_all_users()
        question = getattr(self.thread, 'question', None)
        if question:
            context['my_choice_id'] = PollVote.objects.filter(
                question=question, user=self.request.user
            ).values_list('choice_id', flat=True).first()
        return context


class PostDetailView(LoginRequiredMixin, DetailView):
    "Displays a single post"
    model = Post

    def get_queryset(self):
        return Post.objects.filter(thread__visible=True)


# Thread and Post creation and edit #
class NewThread(LoginRequiredMixin, PreviewPostMixin, CategoryReadMixin,
                CreateView):
    form_class = PostForm
    template_name = 'forum/thread_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(
            Category, slug=kwargs['category_slug'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Pass Category from url to context"""
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['static_url'] = settings.STATIC_URL
        context['users'] = get_all_users()
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
            category__slug=kwargs['category_slug'],
            visible=True)
        if self.thread.isLocked and not request.user.is_staff:
            raise PermissionDenied
        self.category = self.thread.category
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        "Pass category and thread from url to context"
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['thread'] = self.thread
        context['history'] = Post.objects.filter(
            thread=self.thread).order_by('-pk')[:10]
        context['users'] = get_all_users()
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
        # QuotePost also carries a `pk` kwarg, which the thread URL rejects.
        thread_kwargs = {'category_slug': self.kwargs['category_slug'],
                         'thread_slug': self.kwargs['thread_slug']}
        return '{}?page=last#{}'.format(
            reverse_lazy('forum:thread', kwargs=thread_kwargs),
            str(self.object.pk)
        )


class QuotePost(NewPost):
    """Quote the content of another post"""

    def dispatch(self, request, *args, **kwargs):
        # The quoted post must be visible and belong to the thread in the URL
        self.p = get_object_or_404(
            Post, pk=kwargs['pk'], thread__visible=True,
            thread__slug=kwargs['thread_slug'],
            thread__category__slug=kwargs['category_slug'])
        self.t = self.p.thread
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        "Pass quoted post content as initial data for form"
        initial = super().get_initial()
        initial_text = re.sub(r'\[quote\][\S|\s]+\[/quote\]\r{0,1}\n{0,1}',
                              '',
                              self.p.content_plain)
        text = "[quote][b]@{:s} a dit :[/b]\n{:s}[/quote]".format(
            self.p.author.username, UserReferences(initial_text).remove_tags())
        initial['content_plain'] = text
        return initial


class EditPost(LoginRequiredMixin, PreviewPostMixin, UpdateView):
    form_class = PostForm
    model = Post
    template_name_suffix = '_edit'

    def dispatch(self, request, *args, **kwargs):
        "Get the right post and thread"
        self.p = get_object_or_404(Post, pk=kwargs['pk'], thread__visible=True)
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
        context['static_url'] = settings.STATIC_URL
        context['users'] = get_all_users()
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
        form.instance.modified = timezone.now()
        return super().form_valid(form)

    def get_success_url(self):
        self.kwargs.pop('pk')  # remove useless pk
        self.kwargs['thread_slug'] = self.t.slug
        return '{}?page={}#{}'.format(
            reverse_lazy('forum:thread', kwargs=self.kwargs),
            get_post_page(self.p),
            self.object.pk
        )


class ResetBookmarks(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if kwargs['pk'] != str(request.user.pk):
            raise PermissionDenied
        else:
            # update all bookmark timestamps to now
            Bookmark.objects.filter(user=request.user)\
                .update(timestamp=timezone.now())
            # record resetDateTime on user
            request.user.resetDateTime = timezone.now()
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
            return HttpResponseRedirect(
                reverse('forum:category', kwargs={'category_slug': t.category}))


class PreviewView(LoginRequiredMixin, DetailView):
    model = Preview

    def get_queryset(self):
        return Preview.objects.filter(author=self.request.user)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        self.object.delete()  # Now the object is loaded, delete it
        return self.render_to_response(context)


# Poll Views #
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
                request.POST['thread-content_plain'], request.user)
        else:
            thread_form = PollThreadForm(request.POST, prefix="thread")
            question_form = QuestionForm(request.POST, prefix="question")
            choices_formset = ChoicesFormSet(request.POST)
            if (thread_form.is_valid() and question_form.is_valid() and
                    choices_formset.is_valid()):
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
                thread_form.save()
                # Complete the poll and save it
                question_form.instance.thread = thread
                question = question_form.save()
                choices_formset = ChoicesFormSet(request.POST,
                                                 instance=question)
                if choices_formset.is_valid():
                    choices_formset.save()
                    # Mark category as read
                    mark_category_read(request.user, category)
                    return HttpResponseRedirect(reverse(
                        'forum:category',
                        kwargs={'category_slug': category_slug}))

    return render(request, 'forum/poll_form.html', {
        'category': category,
        'category_slug': category_slug,
        'choices_formset': choices_formset,
        'formset_helper': formset_helper,
        'question_form': question_form,
        'static_url': settings.STATIC_URL,
        'thread_form': thread_form,
        'users': get_all_users(),
    })


@login_required
@require_POST
def VotePoll(request, category_slug, thread_slug):
    thread = get_object_or_404(Thread,
                               slug=thread_slug,
                               category__slug=category_slug,
                               visible=True)
    question = get_object_or_404(PollQuestion, thread=thread)

    try:
        choice_pk = int(request.POST.get('choice', ''))
    except ValueError:
        choice_pk = None

    with transaction.atomic():
        # Serialise votes on this poll: re-check voters inside the lock
        question = PollQuestion.objects.select_for_update().get(pk=question.pk)
        if choice_pk is None or \
                not question.choices.filter(pk=choice_pk).exists():
            messages.error(request, "Aucun choix sélectionné.")
        elif question.voters.filter(pk=request.user.pk).exists():
            messages.error(request, "Vous avez déjà voté.")
        else:
            PollChoice.objects.filter(pk=choice_pk).update(
                votes=F('votes') + 1)
            question.voters.add(request.user)
            PollVote.objects.create(
                question=question, user=request.user, choice_id=choice_pk)
    return HttpResponseRedirect(reverse(
        'forum:thread', kwargs={'category_slug': category_slug,
                                'thread_slug': thread_slug}))


# Search View #
class SearchView(LoginRequiredMixin, ThreadStatusMixin, ListView):
    paginate_by = 30
    paginate_orphans = 2
    template_name = 'forum/search_results.html'

    def get(self, request, *args, **kwargs):
        """Return an error message if the query was empty."""
        self.query = request.GET.get('q', '').strip()
        self.cls = Thread
        if re.match(r'user:', self.query):
            self.entry_query = get_query(self.query[5:], ['author__username'])
        elif re.match(r'post:', self.query):
            self.cls = Post
            self.entry_query = get_query(self.query[5:], ['content_plain'])
        else:
            self.entry_query = get_query(self.query, ['title'])
        if self.entry_query is None:
            messages.error(request, "Aucun terme précisé pour la recherche.")
            return HttpResponseRedirect(reverse('forum:top'))
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """Handle search parameters & process search computation."""
        cls = self.cls
        results = cls.objects.filter(self.entry_query)
        if cls is Post:
            results = results.filter(thread__visible=True)\
                .select_related('author', 'thread__category')
        else:
            results = results.filter(visible=True)\
                .select_related('author', 'category', 'question')
        self.results_count = results.count()
        if not self.results_count:
            messages.error(
                self.request,
                'Aucun résultat ne correspond à cette recherche.'
            )
        else:
            messages.success(
                self.request,
                "{} résultat(s) trouvé(s).".format(self.results_count)
            )
        return results

    def get_context_data(self, **kwargs):
        """Add context data for the template."""
        model = self.object_list.model._meta.model_name
        if model == 'thread':
            context = super().get_context_data(**kwargs)
        else:
            context = ListView.get_context_data(self, **kwargs)
            add_post_pages(context['object_list'])
        context['model'] = model
        context['query'] = self.query
        context['results_count'] = self.results_count
        context['query_url'] = urlencode({'q': self.query}) + '&'
        return context

# UserMentionsView #
class UserMentionsView(LoginRequiredMixin, ListView):
    paginate_by = 30
    paginate_orphans = 2
    template_name = 'forum/user_mentions.html'

    def get_queryset(self):
        """Handle search parameters & process search computation."""
        results = Post.objects\
            .filter(mentions__user=self.request.user, thread__visible=True)\
            .select_related('author', 'thread__category')\
            .order_by("-mentions__pk")
        self.request.user.newMention = False
        self.request.user.save()
        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        add_post_pages(context['object_list'])
        return context
