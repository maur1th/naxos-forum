from django.views.generic import ListView

from braces.views import LoginRequiredMixin

from .models import Category, Thread, Post
from user.models import ForumUser


class Welcome(LoginRequiredMixin, ListView):
    template_name = "forum/welcome.html"
    model = ForumUser


class CategoryView(LoginRequiredMixin, ListView):
    template_name = "forum/categories.html"
    model = Category


class ThreadView(LoginRequiredMixin, ListView):
    template_name = "forum/threads.html"
    model = Thread
