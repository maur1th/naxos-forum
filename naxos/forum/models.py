from django.db import models
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

from datetime import datetime
from uuslug import uuslug

from .util import convert_text_to_html, smilify, keygen
from user.models import ForumUser

SLUG_LENGTH = 50

DATA_SCHEMA_REVISION = 2


### Basic Forum models ###
class Category(models.Model):
    """Contains threads."""
    slug = models.SlugField(blank=False, unique=True, db_index=True)
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
    modified = models.DateTimeField(default=datetime.now)
    category = models.ForeignKey(Category, related_name='threads')
    icon = models.CharField(
        max_length=80, default="icon1.gif", verbose_name='Icône')
    isSticky = models.BooleanField(default=False)
    isLocked = models.BooleanField(default=False)
    isRemoved = models.BooleanField(default=False)
    viewCount = models.IntegerField(default=0)
    latest_post = models.ForeignKey('Post', related_name='+', null=True)

    def save(self, *args, **kwargs):
        """Custom save to create a slug from title"""
        self.slug = uuslug(self.title,
                           filter_dict={'category': self.category},
                           instance=self,
                           max_length=SLUG_LENGTH)
        if not self.slug:  # Prevent empty strings as slug
            self.slug = uuslug('sans titre',
                               filter_dict={'category': self.category},
                               instance=self,
                               max_length=SLUG_LENGTH)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-isSticky", "-modified", "pk"]
        index_together = ['category', 'slug']
        # Permit category.threads.latest in template
        get_latest_by = "modified"

    def __str__(self):
        return "{:s}/{:s}".format(self.category.slug, self.slug)


class Post(models.Model):
    """A post."""
    created = models.DateTimeField(default=datetime.now,
                                   editable=False)
    modified = models.DateTimeField(blank=True, null=True)
    content_plain = models.TextField(verbose_name='Message')
    markup = models.TextField(default='bbcode')
    author = models.ForeignKey(ForumUser, related_name='posts')
    thread = models.ForeignKey(Thread, related_name='posts')

    def save(self, *args, **kwargs):
        new_post = True if self.pk is None else False
        self.thread.contributors.add(self.author)
        super().save(*args, **kwargs)
        if new_post:  # update thread
            self.thread.modified = self.created
            self.thread.latest_post = self
            # latest post has changed, remove template fragment from cache
            key = make_template_fragment_key('thread_latest_post',
                                             [self.thread.pk])
            cache.delete(key)
            key = make_template_fragment_key('thread_post_count',
                                             [self.thread.pk])
            cache.delete(key)
            # caches thread's contributors
            cache.set("{:d}/contributors".format(self.thread.pk),
                  self.thread.contributors.all(),
                  None)
        else:  # modified, remove template fragment from cache
            key = make_template_fragment_key('post', [self.pk])
            cache.delete(key)
        self.thread.save()

    @property
    def html(self):
        content_html = convert_text_to_html(self.content_plain)
        content_html = smilify(content_html)
        return content_html
    
    @property
    def position(self):
        return Post.objects.filter(thread=self.thread).filter(
                                   pk__lt=self.pk).count()

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
        self.content_html = convert_text_to_html(self.content_plain)
        self.content_html = smilify(self.content_html)
        super().save(*args, **kwargs)

    def __str__(self):
        return "{:d}".format(self.pk)


class ThreadCession(models.Model):
    thread = models.OneToOneField(Thread)
    token = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        queryset = self.__class__.objects.all()
        self.token = keygen()
        while queryset.filter(token=self.token).exists():
            self.token = keygen()
        super().save(*args, **kwargs)

    def __str__(self):
        return thread


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
