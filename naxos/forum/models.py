from django.db import models
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_save
from django.dispatch import receiver

from datetime import datetime
from uuslug import uuslug

from .util import convert_text_to_html, smilify, keygen
from user.models import ForumUser, Bookmark

SLUG_LENGTH = 50


### Abstract models ###
class CachedAuthorModel(models.Model):
    """Gets author from cache else from db and create cache"""

    @property
    def cached_author(self):
        author = cache.get('user/{}'.format(self.author_id))
        if not author:
            author = ForumUser.objects.get(pk=self.author_id)
            cache.set('user/{}'.format(self.author_id), author, None)
        return author

    class Meta:
        abstract = True


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


class Thread(CachedAuthorModel):
    """Contains posts."""
    slug = models.SlugField(max_length=SLUG_LENGTH)
    title = models.CharField(max_length=140, verbose_name='Titre')
    author = models.ForeignKey(ForumUser, related_name='threads')
    contributors = models.ManyToManyField(ForumUser)
    category = models.ForeignKey(Category, related_name='threads')
    icon = models.CharField(
        max_length=80, default="icon1.gif", verbose_name='Icône')
    isSticky = models.BooleanField(default=False)
    isLocked = models.BooleanField(default=False)
    isRemoved = models.BooleanField(default=False)
    viewCount = models.IntegerField(default=0)
    postCount = models.IntegerField(default=0)
    modified = models.DateTimeField(default=datetime.now)
    personal = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    cessionToken = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):

        def make_slug(self, title):
            slug = uuslug(title,
                          filter_dict={'category': self.category},
                          instance=self,
                          max_length=SLUG_LENGTH)
            return slug

        def create_token(self):
            queryset = self.__class__.objects.all()
            while True:
                token = keygen()
                if not queryset.filter(cessionToken=token).exists():
                    return token

        new_slug = make_slug(self, self.title)
        if self.pk is not None:  # This is an existing thread
            orig = Thread.objects.get(pk=self.pk)
            # Delete template cache when needed and create new slug
            if orig.slug != new_slug or orig.icon != self.icon:
                self.slug = new_slug
                key = make_template_fragment_key(
                    'thread', [self.pk])
                cache.delete(key)  # Fails silently
            # Change cessionToken if the author has changed or db migration
            if orig.author != self.author or self.cessionToken == 'tmp':
                self.cessionToken = create_token(self)
        else:  # This is a new thread
            # Create slug
            self.slug = new_slug
            # Create initial cessionToken
            self.cessionToken = create_token(self)
        if not self.slug:  # Prevent slugs to be empty
            self.slug = make_slug(self, 'sans titre')
        super().save(*args, **kwargs)

    @property
    def latest_post(self):
        latest_post = cache.get('thread/{}/latest_post'.format(self.pk))
        if not latest_post:
            latest_post = self.posts.latest()
            cache.set(
                'thread/{}/latest_post'.format(self.pk), latest_post, None)
        return latest_post

    class Meta:
        ordering = ["-isSticky", "-modified", "pk"]
        index_together = ['category', 'slug']
        # Permit category.threads.latest in template
        get_latest_by = "modified"

    def __str__(self):
        return "{}/{}".format(self.category.slug, self.slug)


class Post(CachedAuthorModel):
    """A post."""
    created = models.DateTimeField(default=datetime.now,
                                   editable=False)
    modified = models.DateTimeField(blank=True, null=True)
    content_plain = models.TextField(verbose_name='Message',
                                     max_length=100000)
    markup = models.CharField(default='bbcode', max_length=10)
    author = models.ForeignKey(ForumUser, related_name='posts')
    thread = models.ForeignKey(Thread, related_name='posts')

    def save(self, *args, **kwargs):
        self.thread.contributors.add(self.author)
        if self.pk is None:  # Which means this is a new post, not an edit
            self.thread.category.postCount += 1
            self.thread.category.save()
            self.thread.modified = self.created
            self.thread.save()
        super().save(*args, **kwargs)

    @property
    def html(self):
        html = cache.get('post/{}/html'.format(self.pk))
        if not html:
            html = convert_text_to_html(self.content_plain, self.markup)
            if self.markup == 'bbcode': html = smilify(html)
            cache.set('post/{}/html'.format(self.pk), html, None)
        return html
    
    class Meta:
        ordering = ["pk"]
        # Permit thread.posts.latest in template
        get_latest_by = "created"

    def __str__(self):
        return "{:s}: {:d}".format(self.author.username, self.pk)


class Preview(models.Model):
    """Contains post previews. Should be empty."""
    content_plain = models.TextField()
    markup = models.TextField(default='bbcode')

    @property
    def html(self):
        html = convert_text_to_html(self.content_plain, self.markup)
        html = smilify(html)
        return html

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
    choice_text = models.CharField(max_length=80)
    votes = models.IntegerField(default=0)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.choice_text


### Model signal handlers ###
@receiver(post_save, sender=Post)
def update_post_cache(created, instance, **kwargs):
    html = convert_text_to_html(instance.content_plain, instance.markup)
    html = smilify(html)
    cache.set("post/{}/html".format(instance.pk), html, None)
    if created:
        cache.set("thread/{}/contributors".format(instance.thread.pk),
                  instance.thread.contributors.all(), None)
        cache.set('thread/{}/latest_post'.format(instance.thread.pk),
                  instance, None)

@receiver(post_save, sender=Post)
def update_thread_cache(created, instance, **kwargs):
    cache.delete(make_template_fragment_key('thread', [instance.thread.pk]))

@receiver(post_save, sender=Thread)
def update_thread_cache(created, instance, **kwargs):
    cache.delete(make_template_fragment_key('thread', [instance.pk]))

@receiver(post_save, sender=Post)
def increment_thread_postCount(created, instance, **kwargs):
    thread = instance.thread
    thread.postCount = thread.posts.count()
    thread.save()


@receiver(post_save, sender=Thread)
def add_bookmark(created, instance, **kwargs):
    if created: Bookmark.objects.update_or_create(user=instance.author,
                                                  thread=instance)
