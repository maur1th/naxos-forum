from django.db import models
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# import logging

# logger = logging.getLogger(__name__)

from uuslug import uuslug

from utils.renderer import UserReferences, render
from .util import keygen
from user.models import ForumUser, Bookmark

SLUG_LENGTH = 50


# Abstract models
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


# Basic Forum models
class Category(models.Model):
    """Contains threads."""
    slug = models.SlugField(blank=False, unique=True, db_index=True)
    title = models.CharField(max_length=50, blank=False)
    subtitle = models.CharField(max_length=200)

    @property
    def post_count(self):
        key = f"category/{self.pk}/post_count"
        count = cache.get(key)
        if not count:
            count = Post.objects.filter(thread__category__pk=self.pk).count()
            cache.set(key, count, None)
        return count

    class Meta:
        ordering = ["pk"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.slug


class Thread(CachedAuthorModel):
    """Contains posts."""
    slug = models.SlugField(max_length=SLUG_LENGTH)
    title = models.CharField(max_length=140, verbose_name='Titre')
    author = models.ForeignKey(
        ForumUser,
        related_name='threads',
        on_delete=models.CASCADE)
    contributors = models.ManyToManyField(ForumUser)
    category = models.ForeignKey(
        Category,
        related_name='threads',
        on_delete=models.CASCADE)
    icon = models.CharField(
        max_length=80,
        default="icon1.gif",
        verbose_name='Icône')
    isSticky = models.BooleanField(default=False)
    isLocked = models.BooleanField(default=False)
    isRemoved = models.BooleanField(default=False)
    viewCount = models.IntegerField(default=0)
    modified = models.DateTimeField(default=timezone.now)
    personal = models.BooleanField(default=False)
    visible = models.BooleanField(default=True)
    cessionToken = models.CharField(max_length=50, unique=True)

    @property
    def post_count(self):
        key = f"thread/{self.pk}/post_count"
        count = cache.get(key)
        if not count:
            count = self.posts.count() - 1
            cache.set(key, count, None)
        return count

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
        indexes = [models.Index(fields=["category", "slug"])]
        # Permit category.threads.latest in template
        get_latest_by = "modified"

    def __str__(self):
        return "{}/{}".format(self.category.slug, self.slug)


class Post(CachedAuthorModel):
    """A post."""
    created = models.DateTimeField(default=timezone.now,
                                   editable=False)
    modified = models.DateTimeField(blank=True, null=True)
    content_plain = models.TextField(verbose_name='Message',
                                     max_length=100000)
    author = models.ForeignKey(
        ForumUser,
        related_name='posts',
        on_delete=models.CASCADE)
    thread = models.ForeignKey(
        Thread,
        related_name='posts',
        on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        self.thread.contributors.add(self.author)
        if self.pk is None:  # Which means this is a new post, not an edit
            self.thread.modified = self.created
            self.thread.save()
        super().save(*args, **kwargs)

    @property
    def html(self):
        html = cache.get('post/{}/html'.format(self.pk))
        if not html:
            html = render(self.content_plain, 'bbcode')
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
        html = render(self.content_plain, self.markup)
        return html

    def __str__(self):
        return "{:d}".format(self.pk)


class UserMentions(models.Model):
    """Track user mentions in posts"""
    user = models.ForeignKey(
        ForumUser,
        related_name='mentions',
        on_delete=models.CASCADE)
    post = models.ForeignKey(
        Post,
        related_name='mentions',
        on_delete=models.CASCADE)

    def __str__(self):
        return "{:s}: {:d}".format(self.user.username, self.post.pk)

    class Meta:
        ordering = ["-pk"]
        unique_together = ("user", "post")
        indexes = [models.Index(fields=["user", "post"])]


# Poll models
class PollQuestion(models.Model):
    question_text = models.CharField(max_length=80)
    thread = models.OneToOneField(
        Thread,
        related_name='question',
        on_delete=models.CASCADE)
    voters = models.ManyToManyField(ForumUser, blank=True)

    def __str__(self):
        return self.question_text


class PollChoice(models.Model):
    question = models.ForeignKey(
        PollQuestion,
        related_name='choices',
        on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=80)
    votes = models.IntegerField(default=0)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return self.choice_text


# Budget
class BudgetRecord(models.Model):
    date = models.DateTimeField(default=timezone.now)
    amount = models.FloatField()
    label = models.CharField(max_length=200)

    class Meta:
        ordering = ["pk"]


# Model signal handlers
@receiver(post_save, sender=Post)
def update_post_cache(created, instance, **kwargs):
    html = render(instance.content_plain, "bbcode")
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
def update_post_count(created, instance, **kwargs):
    if created:
        category = instance.thread.category.pk
        thread = instance.thread.pk
        cache.set(f"category/{category}/post_count",
                  Post.objects.filter(thread__category__pk=category).count(),
                  None)
        cache.set(f"thread/{thread}/post_count",
                  instance.thread.posts.count() - 1,
                  None)


@receiver(post_save, sender=Post)
def add_user_mentions(created, instance, **kwargs):
    for user in UserReferences(instance.content_plain).get_users():
        obj, created = UserMentions.objects.get_or_create(user=user, post=instance)
        if created:
            user.newMention = True
            user.save()
        # logger.warning(obj)


@receiver(post_save, sender=Thread)
def add_bookmark(created, instance, **kwargs):
    if created:
        Bookmark.objects.update_or_create(
            user=instance.author,
            thread=instance
        )
