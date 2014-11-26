from django.views.generic import ListView, CreateView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from braces.views import LoginRequiredMixin

from .models import Conversation
from .forms import ConversationForm


### PM views ###
class PMTopView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = "messages/top.html"


class NewConversation(LoginRequiredMixin, CreateView):
    form_class = ConversationForm
    template_name = "messages/new_conversation.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    # def get_form_kwargs(self):
    #     kwargs = super(NewPost, self).get_form_kwargs()
    #     kwargs.update({'category_slug': self.kwargs['category_slug'],
    #                    'thread': self.t})
    #     return kwargs


# class NewPvtConversation(LoginRequiredMixin, CreateView):
#     form_class = ConversationForm
#     template_name = 'forum/new_conversation.html'

#     def dispatch(self, request, *args, **kwargs):
#         return super().dispatch(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):
#         "Pass Category from url to context"
#         context = super().get_context_data(**kwargs)
#         context['category'] = self.c
#         return context

#     def form_valid(self, form):
#         "Handle thread and 1st post creation in the db"
#         # Create the thread
#         t = Conversation.objects.create(
#             title=self.request.POST['title'],
#             author=self.request.user,
#             category=self.c)
#         # Complete the post and save it
#         form.instance.thread = t
#         form.instance.author = self.request.user
#         m = form.save()
#         self.request.user.postsReadCaret.add(m)
#         return HttpResponseRedirect(self.get_success_url())

#     def get_success_url(self):
#         return reverse('forum:top')
