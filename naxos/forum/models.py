import datetime
from django.db import models

from uuslug import uuslug

from user.models import ForumUser


# TODO
# Improve TZ support


class Category(models.Model):
    """Contains threads."""
    slug = models.SlugField(blank=False)
    title = models.CharField(max_length=50, blank=False)
    subtitle = models.CharField(max_length=200)
    threadCount = models.IntegerField(default=0)
    postCount = models.IntegerField(default=0)
    lastMessage = models.CharField(max_length=140)
    lastMessageUrl = models.URLField()

    def __str__(self):
        return self.slug


class Thread(models.Model):
    """Contains posts."""
    slug = models.SlugField(max_length=50, unique=True)
    title = models.CharField(max_length=140)
    author = models.ForeignKey(ForumUser, related_name='threads')
    modified = models.DateTimeField(default=datetime.datetime.now)
    category = models.ForeignKey(Category, related_name='threads')
    icon = models.ImageField()
    isSticky = models.BooleanField(default=False)
    isLocked = models.BooleanField(default=False)
    isRemoved = models.BooleanField(default=False)
    postCount = models.IntegerField(default=0)
    viewCount = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        """Custom save to create a slug from title"""
        self.slug = uuslug(self.title, instance=self, max_length=50)
        super(Thread, self).save(*args, **kwargs)

    class Meta:
        ordering = ["-modified"]

    def __str__(self):
        return self.slug


class Post(models.Model):
    """A post."""
    created = models.DateTimeField(default=datetime.datetime.now,
                                   editable=False)
    modified = models.DateTimeField(blank=True, null=True)
    content_plain = models.TextField()
    content_html = models.TextField()
    author = models.ForeignKey(ForumUser, related_name='posts')
    thread = models.ForeignKey(Thread, related_name='posts')

    def __str__(self):
        end = len(self.content_plain) > 40 and "..." or ""
        return "{:s}: {:s}{:s}".format(self.author.username,
                                       self.content_plain[:40], end)

    class Meta:
        ordering = ["created"]

    def save(self, *args, **kwargs):
        self.content_html = self.content_plain
        super(Post, self).save(*args, **kwargs)
