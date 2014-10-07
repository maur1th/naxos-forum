from django.views.generic import TemplateView
from django.core.urlresolvers import reverse_lazy

from braces.views import LoginRequiredMixin


class Welcome(LoginRequiredMixin, TemplateView):
    template_name = "forum/welcome.html"
    login_url = reverse_lazy('user:login')

    def get(self, request):
        return self.render_to_response({})
