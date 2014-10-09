from django.views.generic import ListView
from user.models import ForumUser
from braces.views import LoginRequiredMixin


class Welcome(LoginRequiredMixin, ListView):
    template_name = "forum/welcome.html"
    model = ForumUser
