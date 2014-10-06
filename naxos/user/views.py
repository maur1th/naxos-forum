from django.views.generic import CreateView
from django.core.urlresolvers import reverse_lazy

from .forms import RegisterForm


class Register(CreateView):
    template_name = 'register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('forum:welcome')
