from datetime import timedelta

from django.views.generic import CreateView, ListView, UpdateView, TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, update_session_auth_hash
from django.http import HttpResponse, HttpResponseRedirect, \
    HttpResponseServerError
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import render
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.views.decorators.http import require_POST
from django.db.models import Count, OuterRef, Subquery
from django.db.models.functions import Lower

from .forms import RegisterForm, UpdateUserForm, CrispyPasswordForm, BudgetRecordForm
from .models import ForumUser
from forum.models import BudgetRecord, Post, Thread


class Register(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('user:login')

    def form_valid(self, form):
        # RegisterForm.save() raises if the key was consumed after validation
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error('token', e)
            return self.form_invalid(form)


class UpdateUser(LoginRequiredMixin, UpdateView):
    form_class = UpdateUserForm
    template_name = 'user/profile.html'

    def get_object(self):
        return ForumUser.objects.get(username=self.request.user)

    def get_form_kwargs(self):
        """Pass user to form."""
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        # Change thread owner if a token has been entered
        token = form.cleaned_data.get('token')
        if token:
            obj = Thread.objects.get(cessionToken=token)
            t, p = obj, obj.posts.first()
            t.author, p.author = self.request.user, self.request.user
            t.save()
            p.save()
            # Update thread cache to reflect author's change
            key = make_template_fragment_key('thread', [t.pk])
            cache.delete(key)
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Paramètres sauvegardés.")
        return reverse('user:profile', kwargs=self.kwargs)


@login_required
def UpdatePassword(request):
    form = CrispyPasswordForm(user=request.user)

    if request.method == 'POST':
        form = CrispyPasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Mot de passe modifié.")

    return render(request, 'user/password.html', {
        'form': form,
    })


class MemberList(LoginRequiredMixin, TemplateView):
    template_name = "user/members.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        latest_post = Post.objects.filter(author=OuterRef('pk'))\
            .order_by('-created').values('created')[:1]
        members = list(ForumUser.objects
                       .annotate(last_post=Subquery(latest_post))
                       .order_by(Lower('username')))
        online = cache.get_many(
            [f"user/{m.pk}/is_online" for m in members])
        for m in members:
            m.online = bool(online.get(f"user/{m.pk}/is_online"))
        context['active_users'] = [m for m in members if m.is_active]
        context['inactive_users'] = [m for m in members if not m.is_active]
        return context


class Top10(LoginRequiredMixin, TemplateView):
    template_name = "user/top10.html"

    def dispatch(self, request, *args, **kwargs):
        threads = Thread.objects.filter(visible=True).annotate(p_count=Count("posts"))
        self.top_views = threads.order_by("-viewCount")[:10]
        self.top_posts = threads.order_by("-p_count")[:10]
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['top_views'] = self.top_views
        context['top_posts'] = self.top_posts
        return context


# Budget #
class BudgetView(LoginRequiredMixin, ListView):
    model = BudgetRecord
    paginate_by = 1000
    template_name = 'user/budgetrecord_list.html'

    def get(self, request, *args, **kwargs):
        if self.request.user.username not in ["admin", "équi"]:
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = BudgetRecordForm()
        return context


class NewBudgetRecord(LoginRequiredMixin, CreateView):
    form_class = BudgetRecordForm

    def post(self, request, *args, **kwargs):
        if self.request.user.username not in ["admin", "équi"]:
            raise PermissionDenied
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('user:budget')


# Online presence heartbeat, sent periodically by naxos.js
ONLINE_TIMEOUT = 90  # seconds without a ping before a user shows as offline
LAST_SEEN_REFRESH = timedelta(minutes=5)


@login_required
@require_POST
def ping(request):
    user = request.user
    cache.set(f"user/{user.pk}/is_online", True, ONLINE_TIMEOUT)
    now = timezone.now()
    if user.last_seen is None or now - user.last_seen > LAST_SEEN_REFRESH:
        ForumUser.objects.filter(pk=user.pk).update(last_seen=now)
    return HttpResponse(status=204)
