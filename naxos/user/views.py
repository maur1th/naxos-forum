from django.views.generic import CreateView
from django.core.urlresolvers import reverse_lazy

from .forms import RegisterForm


class Register(CreateView):
    form_class = RegisterForm
    template_name = 'user/register.html'
    success_url = reverse_lazy('user:login')
