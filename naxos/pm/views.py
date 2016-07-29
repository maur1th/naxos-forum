from django.shortcuts import get_object_or_404
from django.views.generic import View, ListView, CreateView
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from user.models import ForumUser
from .models import Conversation, Message
from .forms import ConversationForm


# Helper stuff
def pm_counter(request, c):
    """Increment conversation recipient's pm counter"""
    recipient = c.participants.exclude(username=request.user).get()
    recipient.pmUnreadCount += 1
    recipient.save()


# PM views
class PMTopView(LoginRequiredMixin, ListView):
    model = Conversation
    paginate_by = 30
    paginate_orphans = 2

    def get_queryset(self):
        self.request.user.pmUnreadCount = 0
        self.request.user.save()
        return Conversation.objects.filter(participants=self.request.user)


class MessageView(LoginRequiredMixin, ListView):

    """Display conversation list of messages"""
    model = Message
    paginate_by = 30
    paginate_orphans = 2

    def get(self, request, *args, **kwargs):
        self.c = get_object_or_404(Conversation, pk=kwargs['pk'])
        # Handle forbidden user
        if request.user not in self.c.participants.all():
            return HttpResponseForbidden()
        # Handle user read caret
        m = self.c.messages.latest()
        try:
            caret = request.user.pmReadCaret.get(conversation=self.c)
        except:
            caret = False
        if caret != m:
            request.user.pmReadCaret.remove(caret)
            request.user.pmReadCaret.add(m)
        return super().get(request, *args, **kwargs)

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
    model = Conversation
    form_class = ConversationForm
    success_url = reverse_lazy('pm:top')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user.pk,
                       'recipient': self.kwargs.get('recipient', 0)})
        return kwargs

    def form_valid(self, form):
        recipient = self.request.POST['recipient']
        # Check if conversation already exists
        query = Conversation.objects\
            .filter(participants=self.request.user)\
            .filter(participants=recipient)
        if query:
            c = query.get()
        else:  # Create the conversation
            c = Conversation()
            c.save()
            c.participants.add(self.request.user, recipient)
        # Complete the message and save it
        form.instance.conversation = c
        form.instance.author = self.request.user
        m = form.save()
        # Add read caret for the author
        self.request.user.pmReadCaret.add(m)
        pm_counter(self.request, c)
        return HttpResponseRedirect(self.success_url)


@login_required
def NewMessage(request, pk):
    if request.method == 'POST':
        c = get_object_or_404(Conversation, pk=pk)
        m = Message.objects.create(
            conversation=c,
            author=request.user,
            content_plain=request.POST['content_plain'])
        pm_counter(request, c)
        qs = '?page=last#' + str(m.pk)
        return HttpResponseRedirect(
            reverse_lazy('pm:msg', kwargs={'pk': pk}) + qs)
    else:
        return HttpResponseRedirect(reverse_lazy('pm:top'))


class DeleteMessage(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        m = get_object_or_404(Message, pk=kwargs['pk'])
        c = m.conversation
        if m.author not in m.conversation.participants.all():
            raise PermissionDenied
        else:
            m.shown = False
            m.save()
            # Set conversation modified timestamp again in case
            # the latest message was the one deleted
            latest_message_shown = c.messages.filter(shown=True)\
                .order_by('created').last()
            if latest_message_shown:
                c.modified = latest_message_shown.created
                c.save()
                return HttpResponseRedirect(
                    reverse('pm:msg', args=[m.conversation.pk]))
            else:
                # If no message is shown return to top
                return HttpResponseRedirect(
                    reverse('pm:top'))


# Search form
@login_required
def GetConversation(request):
    """Conversation search form"""
    if request.method == 'POST':
        u = ForumUser.objects.exclude(username=request.user)\
            .filter(username__istartswith=request.POST['query'])
        if u.count() == 1:
            c = Conversation.objects.filter(participants=request.user)\
                .filter(participants=u.get())
            if c.count() == 1:
                c = c.get()
                tag = '#' + str(c.messages.latest().pk)
                return HttpResponseRedirect(
                    reverse_lazy('pm:msg', kwargs={'pk': c.pk}) + tag)
            else:
                messages.error(
                    request,
                    ("Il n'existe pas de conversation avec"
                        " cet utilisateur : {:s}.".format(u.get().username))
                )
        elif u.count() > 1:
            messages.error(
                request,
                "Plusieurs utilisateurs possibles : {:s}.".format(
                    ", ".join([u.username for u in u]))
            )
        else:
            messages.error(request, "Aucun utilisateur trouvé.")
    return HttpResponseRedirect(reverse_lazy('pm:top'))
