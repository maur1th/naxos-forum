from django.db import models
from django.core.exceptions import ValidationError
from django.core.cache import cache

import datetime

from user.models import ForumUser
from forum.util import convert_text_to_html, smilify


# PM models
class Conversation(models.Model):
    """Contains PMs between two participants"""

    participants = models.ManyToManyField(ForumUser, blank=False)
    modified = models.DateTimeField(default=datetime.datetime.now)
    isRemoved = models.BooleanField(default=False)

    @property
    def latest_shown_message(self):
        return self.messages.filter(shown=True).order_by('created').last()

    @property
    def shown_message_count(self):
        return self.messages.filter(shown=True).count()

    class Meta:
        ordering = ["-modified"]
        get_latest_by = "modified"

    def __str__(self):
        return str([user.username for user in self.participants.all()])


class Message(models.Model):

    """A message."""
    created = models.DateTimeField(default=datetime.datetime.now,
                                   editable=False)
    content_plain = models.TextField(verbose_name='Message')
    markup = models.TextField(default='bbcode')
    author = models.ForeignKey(
        ForumUser,
        related_name='pvt_messages',
        on_delete=models.CASCADE)
    conversation = models.ForeignKey(
        Conversation,
        related_name='messages',
        on_delete=models.CASCADE)
    shown = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Update conv datetime
        self.conversation.modified = self.created
        self.conversation.save()
        super().save(*args, **kwargs)

    @property
    def html(self):
        html = cache.get('message/{}/html'.format(self.pk))
        if not html:
            html = convert_text_to_html(self.content_plain, self.markup)
            if self.markup == 'bbcode':
                html = smilify(html)
            cache.set('message/{}/html'.format(self.pk), html, None)
        return html

    class Meta:
        ordering = ["created"]
        # Permit thread.posts.latest in template
        get_latest_by = "created"

    def __str__(self):
        return "{:s}: {:d}".format(self.author.username, self.pk)
