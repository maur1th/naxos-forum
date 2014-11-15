from django.views.generic import CreateView, UpdateView, ListView
from django.core.urlresolvers import reverse_lazy

from braces.views import LoginRequiredMixin

from .forms import RegisterForm,  UpdateUserForm
from .models import ForumUser


class Register(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('user:login')


class UpdateUser(LoginRequiredMixin, UpdateView):
    form_class = UpdateUserForm
    template_name = 'user/profile.html'
    success_url = reverse_lazy('user:profile')

    def get_object(self):
        return ForumUser.objects.get(username=self.request.user)

    def get_form_kwargs(self):
        """Pass request to form."""
        kwargs = super(UpdateUser, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs


class MemberList(LoginRequiredMixin, ListView):
    template_name = "user/members.html"
    model = ForumUser
