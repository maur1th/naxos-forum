from django.views.generic import CreateView, UpdateView, FormView, ListView
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, update_session_auth_hash
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from datetime import datetime
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.http import HttpResponse, HttpResponseServerError
from django.contrib.sessions.models import Session
from django.views.decorators.csrf import csrf_exempt

from braces.views import LoginRequiredMixin

from .forms import RegisterForm, UpdateUserForm, CrispyPasswordForm
from .models import ForumUser
from forum.models import Thread


class Register(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('user:login')


class UpdateUser(LoginRequiredMixin, UpdateView):
    form_class = UpdateUserForm
    template_name = 'user/profile.html'

    def get_object(self):
        return ForumUser.objects.get(username=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['donate'] = True
        return context

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
            t, p = obj.thread, obj.thread.posts.first()
            t.author, p.author = self.request.user, self.request.user
            t.save()
            p.save()
            # Update thread cache to reflect author's change
            key = make_template_fragment_key('thread', [self.t.pk])
            cache.delete(key)
            obj.delete()  # Delete cession token
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


class MemberList(LoginRequiredMixin, ListView):
    template_name = "user/members.html"
    context_object_name = "active_users"

    def dispatch(self, request, *args, **kwargs):
        qs = ForumUser.objects.extra(
            select={'username_lower': 'lower(username)'}).order_by(
            'username_lower')
        self.active_users = qs.filter(is_active=True)
        self.inactive_users = qs.filter(is_active=False)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.active_users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inactive_users'] = self.inactive_users
        return context


# Set disconnection timestamp
@csrf_exempt
def node_api(request):
    session = Session.objects.get(
        session_key=request.POST['sessionid'])
    user_id = session.get_decoded().get('_auth_user_id')
    status = request.POST['status']
    try:
        user = ForumUser.objects.get(pk=user_id)
    except ForumUser.DoesNotExist:
        return HttpResponseServerError()
    if status == 'connected':
        user.is_online = True
    elif status == 'disconnected':
        user.is_online = False
    user.last_seen = datetime.now()
    user.save()
    return HttpResponse()  # So we don't log a 500 error
