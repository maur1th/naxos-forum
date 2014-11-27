from django.views.generic import ListView, CreateView
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth.decorators import login_required

from braces.views import LoginRequiredMixin

from .models import Conversation, Message
from .forms import ConversationForm


### PM views ###
class PMTopView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = "messages/top.html"

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)


class MessageView(LoginRequiredMixin, ListView):

    """Display conversation list of messages"""
    template_name = "messages/messages.html"
    model = Message
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        self.c = Conversation.objects.get(pk=self.kwargs['pk'])
        # Handle forbidden user
        if self.request.user not in self.c.participants.all():
            return HttpResponseForbidden()
        # Handle user read caret
        m = self.c.messages.latest()
        try:
            caret = self.request.user.pmReadCaret.get(conversation=self.c)
        except:
            caret = False
        if caret != m:
            self.request.user.pmReadCaret.remove(caret)
            self.request.user.pmReadCaret.add(m)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Message.objects.filter(conversation=self.c).all()

    def get_context_data(self, **kwargs):
        "Pass recipient to context"
        context = super().get_context_data(**kwargs)
        context['recipient'] = self.c.participants.exclude(
            username=self.request.user).get()
        context['conversation'] = self.c
        return context


class NewConversation(LoginRequiredMixin, CreateView):
    form_class = ConversationForm
    template_name = "messages/new_conversation.html"
    success_url = reverse_lazy('pm:top')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        recipient = self.request.POST['recipient']
        query = Conversation.objects.filter(
                    participants=self.request.user).filter(
                    participants=recipient)
        if query:
            c = query.get()
        else:
            # Create the conversation
            c = Conversation()
            c.save()
            c.participants.add(self.request.user, recipient)
        # Complete the message and save it
        form.instance.conversation = c
        form.instance.author = self.request.user
        return super().form_valid(form)


@login_required
def NewMessage(request, pk):
    if request.method == 'POST':
        m = Message.objects.create(
                conversation = Conversation.objects.get(pk=pk),
                author = request.user,
                content_plain=request.POST['content_plain'])
        return HttpResponseRedirect(reverse_lazy('pm:msg',
            kwargs={'pk': pk}) + '#' + str(m.pk))

    else:
        return HttpResponseRedirect(reverse_lazy('pm:top'))
