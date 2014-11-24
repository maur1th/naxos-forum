from django.views.generic import ListView

from braces.views import LoginRequiredMixin

from .models import Conversation
from .forms import ConversationForm


### PM views ###
class PMTopView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = "messages/top.html"


# class NewPvtConversation(LoginRequiredMixin, CreateView):
#     form_class = PvtConversationForm
#     template_name = 'forum/new_conversation.html'

#     def dispatch(self, request, *args, **kwargs):
#         self.c = Category.objects.get(slug=self.kwargs['category_slug'])
#         return super(NewThread, self).dispatch(request, *args, **kwargs)

#     def get_context_data(self, **kwargs):
#         "Pass Category from url to context"
#         context = super(NewThread, self).get_context_data(**kwargs)
#         context['category'] = self.c
#         return context

#     def get_form_kwargs(self):
#         kwargs = super(NewThread, self).get_form_kwargs()
#         kwargs.update({'category_slug': self.kwargs['category_slug']})
#         return kwargs

#     def form_valid(self, form):
#         "Handle thread and 1st post creation in the db"
#         # Create the thread
#         t = PvtConversation.objects.create(
#             title=self.request.POST['title'],
#             author=self.request.user,
#             category=self.c)
#         # Complete the post and save it
#         form.instance.thread = t
#         form.instance.author = self.request.user
#         p = form.save()
#         self.request.user.postsReadCaret.add(p)
#         return HttpResponseRedirect(self.get_success_url())

#     def get_success_url(self):
#         return reverse_lazy('forum:category', kwargs=self.kwargs)
