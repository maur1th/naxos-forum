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

from braces.views import LoginRequiredMixin

from .forms import RegisterForm, UpdateUserForm, CrispyPasswordForm, \
    CrispyAuthForm
from .models import ForumUser
from forum.models import ThreadCession


class Register(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('user:login')


class Login(FormView):
    form_class = CrispyAuthForm
    template_name = 'registration/login.html'
    success_url = reverse_lazy('forum:top')

    def dispatch(self, request, *args, **kwargs):
        request.session.set_test_cookie()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        auth_login(self.request, form.get_user())
        if self.request.session.test_cookie_worked():
            self.request.session.delete_test_cookie()
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


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
            obj = ThreadCession.objects.get(token=token)
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
        context['creation'] = datetime(2015, 1, 28, 15, 5)
        return context
