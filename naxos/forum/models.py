from django.db import models

import datetime
from uuslug import uuslug

from .util import convert_text_to_html, smilify
from user.models import ForumUser

SLUG_LENGTH = 50


### Basic Forum models ###
class Category(models.Model):
    """Contains threads."""
    slug = models.SlugField(blank=False, unique=True)
    title = models.CharField(max_length=50, blank=False)
    subtitle = models.CharField(max_length=200)
    postCount = models.IntegerField(default=0)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.slug


class Thread(models.Model):
    """Contains posts."""
    slug = models.SlugField(max_length=SLUG_LENGTH)
    title = models.CharField(max_length=80, verbose_name='Titre')
    author = models.ForeignKey(ForumUser, related_name='threads')
    contributors = models.ManyToManyField(ForumUser)
    modified = models.DateTimeField(default=datetime.datetime.now)
    category = models.ForeignKey(Category, related_name='threads')
    icon = models.CharField(
        max_length=80, default="icon1.gif", verbose_name='Icône')
    isSticky = models.BooleanField(default=False)
    isLocked = models.BooleanField(default=False)
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
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-isSticky", "-modified", "pk"]
        index_together = ['category', 'slug']
        # Permit thread.posts.latest in template
        get_latest_by = "modified"

    def __str__(self):
        return "{:s}/{:s}".format(self.category.slug, self.slug)


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
        self.content_html = smilify(self.content_html)
        self.thread.contributors.add(self.author)
        self.thread.save()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["pk"]
        # Permit thread.posts.latest in template
        get_latest_by = "created"

    def __str__(self):
        return "{:s}: {:d}".format(self.author.username, self.pk)


class Preview(models.Model):
    """Contains post previews. Should be empty."""
    content_plain = models.TextField()
    content_html = models.TextField()

    def save(self, *args, **kwargs):
        Preview.objects.all().delete()  # Just in case
        self.content_html = convert_text_to_html(self.content_plain)
        self.content_html = smilify(self.content_html)
        super().save(*args, **kwargs)

    def __str__(self):
        return "{:d}".format(self.pk)
        

### Poll models ###
class PollQuestion(models.Model):
    question_text = models.CharField(max_length=80)
    thread = models.OneToOneField(Thread, related_name='question')
    voters = models.ManyToManyField(ForumUser, blank=True)

    def __str__(self):
        return self.question_text


class PollChoice(models.Model):
    question = models.ForeignKey(PollQuestion, related_name='choices')
    choice_text = models.CharField(max_length=40)
    votes = models.IntegerField(default=0)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.choice_text
