from django.db import models
from django.core.exceptions import ValidationError

import datetime

from user.models import ForumUser
from forum.util import convert_text_to_html, smilify


# PM models
class Conversation(models.Model):
    """Contains PMs between two participants"""

    participants = models.ManyToManyField(ForumUser, blank=False)
    modified = models.DateTimeField(default=datetime.datetime.now)
    isRemoved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-modified"]
        # Permit thread.posts.latest in template
        get_latest_by = "modified"

    def __str__(self):
        return str([user.username for user in self.participants.all()])


class Message(models.Model):

    """A message."""
    created = models.DateTimeField(default=datetime.datetime.now,
                                   editable=False)
    content_plain = models.TextField(verbose_name='Message')
    content_html = models.TextField()
    markup = models.TextField(default='bbcode')
    author = models.ForeignKey(ForumUser, related_name='pvt_messages')
    conversation = models.ForeignKey(Conversation, related_name='messages')

    def save(self, *args, **kwargs):
        # BBCode + Smileys
        self.content_html = convert_text_to_html(self.content_plain)
        self.content_html = smilify(self.content_html)
        # Update conv datetime
        self.conversation.modified = self.created
        self.conversation.save()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["created"]
        # Permit thread.posts.latest in template
        get_latest_by = "created"

    def __str__(self):
        return "{:s}: {:d}".format(self.author.username, self.pk)
