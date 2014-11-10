from django.db import models


class Conversation(models.Model):

    """Contains messages."""
    author = models.ForeignKey(ForumUser, related_name='conversations')
    recipient = models.ForeignKey(ForumUser, related_name='conversations')
    isRemoved = models.BooleanField(default=False)
    viewCount = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        """Custom save to create a slug from title"""
        self.slug = uuslug(self.title,
                           filter_dict={'category': self.category},
                           instance=self,
                           max_length=SLUG_LENGTH)
        if not self.slug:
            self.slug = uuslug('sans titre',
                               filter_dict={'category': self.category},
                               instance=self,
                               max_length=SLUG_LENGTH)
        super(Thread, self).save(*args, **kwargs)


class Post(models.Model):

    """A post."""
    created = models.DateTimeField(default=datetime.datetime.now,
                                   editable=False)
    modified = models.DateTimeField(blank=True, null=True)
    content_plain = models.TextField(verbose_name='Message')
    content_html = models.TextField()
    markup = models.TextField(default='bbcode')
    author = models.ForeignKey(ForumUser, related_name='posts')
    thread = models.ForeignKey(Thread, related_name='posts')

    def save(self, *args, **kwargs):
        self.content_html = convert_text_to_html(self.content_plain)
        super(Post, self).save(*args, **kwargs)

    class Meta:
        ordering = ["created"]
        # Permit thread.posts.latest in template
        get_latest_by = "created"

    def __str__(self):
        return "{:s}: {:d}".format(self.author.username, self.pk)