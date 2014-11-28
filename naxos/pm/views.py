from django.views.generic import ListView, CreateView
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from braces.views import LoginRequiredMixin

from user.models import ForumUser
from .models import Conversation, Message
from .forms import ConversationForm


### Helper ###
def pm_counter(request, c):
    """Increment conversation recipient pm counter"""
    recipient = c.participants.exclude(username=request.user).get()
    recipient.pmUnreadCount += 1
    recipient.save()


### PM views ###
class PMTopView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = "messages/top.html"

    def dispatch(self, request, *args, **kwargs):
        self.request.user.pmUnreadCount = 0
        self.request.user.save()
        return super().dispatch(request, *args, **kwargs)

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
        # Check if conversation already exists
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
        m = form.save()
        self.request.user.pmReadCaret.add(m)
        pm_counter(self.request, c)
        return HttpResponseRedirect(self.success_url)


@login_required
def NewMessage(request, pk):
    if request.method == 'POST':
        c = Conversation.objects.get(pk=pk)
        m = Message.objects.create(
                conversation = c,
                author = request.user,
                content_plain=request.POST['content_plain'])
        pm_counter(request, c)
        return HttpResponseRedirect(reverse_lazy('pm:msg',
            kwargs={'pk': pk}) + '#' + str(m.pk))

    else:
        return HttpResponseRedirect(reverse_lazy('pm:top'))

@login_required
def GetConversation(request):
    if request.method == 'POST':
        u = ForumUser.objects.exclude(username=request.user).filter(
                username__istartswith=request.POST['query'])
        if u.count() == 1:
            c = Conversation.objects.filter(participants=request.user).filter(
                    participants=u.get())
            if c.count() == 1:
                c = c.get()
                return HttpResponseRedirect(reverse_lazy('pm:msg',
                    kwargs={'pk': c.pk}) + '#' + str(c.messages.latest().pk))
            else:
                messages.error(request, "Il n'existe pas de conversation avec cet utilisateur.")
        elif u.count() > 1:
            messages.error(request,
                "Plusieurs utilisateurs possibles : {:s}.".format(
                    ", ".join([u.username for u in u])))
        else:
            messages.error(request, "Aucun utilisateur trouvé.")
    
    return HttpResponseRedirect(reverse_lazy('pm:top'))
