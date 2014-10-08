from django.views.generic import CreateView, UpdateView
from django.core.urlresolvers import reverse_lazy

from braces.views import LoginRequiredMixin

from django.contrib.auth.models import User
from .models import UserSettings
from .forms import RegisterForm


class Register(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('user:login')


class EditUser(LoginRequiredMixin, UpdateView):
    model = UserSettings
    fields = ('emailVisible', 'subscribeToMails', 'mpPopupNotif',
              'mpEmailNotif', 'avatar', 'quote', 'website')
    template_name = 'user/edit.html'

    def get_object(self):
        return UserSettings.objects.get(user_id=self.request.user)

    def get_success_url(self):
        return reverse_lazy('user:edit')
