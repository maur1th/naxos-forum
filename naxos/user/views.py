from django.views.generic import CreateView, UpdateView
from django.core.urlresolvers import reverse_lazy

from braces.views import LoginRequiredMixin

from .forms import RegisterForm
from .models import ForumUser


class Register(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('user:login')


class EditUser(LoginRequiredMixin, UpdateView):
    model = ForumUser
    fields = ('email', 'emailVisible', 'subscribeToEmails', 'mpPopupNotif',
              'mpEmailNotif', 'logo', 'quote', 'website')
    template_name = 'user/edit.html'
    success_url = reverse_lazy('forum:welcome')

    def get_object(self):
        return ForumUser.objects.get(username=self.request.user)
