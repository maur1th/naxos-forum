from django.views.generic import ListView
from django.contrib.auth.models import User

from braces.views import LoginRequiredMixin


class Welcome(LoginRequiredMixin, ListView):
    template_name = "forum/welcome.html"
    model = User
