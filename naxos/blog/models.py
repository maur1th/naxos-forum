from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.urlresolvers import reverse

import os
from uuslug import uuslug
from socket import gethostname

from forum.util import convert_text_to_html
from forum.models import Category, Thread, Post, SLUG_LENGTH
from user.models import ForumUser


def import_from(module, name):
    module = __import__(module, fromlist=[name])
    return getattr(module, name)

SITE_URL = import_from(
    os.environ.get("DJANGO_SETTINGS_MODULE"), 'SITE_URL')
ROBOT_NAME = import_from(
    os.environ.get("DJANGO_SETTINGS_MODULE"), 'ROBOT')


class BlogPost(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=80, verbose_name='Titre')
    author = models.ForeignKey(ForumUser, related_name='blogposts')
    content = models.TextField(verbose_name='Message',
                               max_length=100000)
    image = models.ImageField(upload_to="images", blank=True, null=True)
    views = models.IntegerField(default=0)
    slug = models.CharField(max_length=SLUG_LENGTH, unique=True)
    forum_thread = models.OneToOneField(
        Thread, null=True, related_name='blog_post')

    def save(self, *args, **kwargs):
        # Create unique slug
        self.slug = uuslug(self.title,
                           instance=self,
                           max_length=SLUG_LENGTH)
        # Prevent empty strings as slug
        if not self.slug:
            self.slug = uuslug('sans titre',
                               instance=self,
                               max_length=SLUG_LENGTH)
        # Delete old image
        try:
            this = BlogPost.objects.get(pk=self.pk)
            if this.image != self.image:
                this.image.delete()
        except:
            pass
        super().save(*args, **kwargs)

    @property
    def html(self):
        return convert_text_to_html(self.content, 'markdown')

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-pk']


# Model signal handlers
@receiver(pre_save, sender=BlogPost)
def new_post_pre_save(instance, **kwargs):
    """Create related thread and link it to the blog post"""
    if instance.pk:
        return
    c = Category.objects.get(slug='jep')
    title = "empty"  # For now, need post pk first
    author = (ForumUser.objects.get(username=ROBOT_NAME) if ROBOT_NAME
              else instance.author)
    t = Thread.objects.create(title=title,
                              author=author,
                              category=c)
    instance.forum_thread = t


@receiver(post_save, sender=BlogPost)
def new_post_post_save(instance, created, **kwargs):
    """Create/Update the thread's first post and its title"""
    # Create or update thread's title
    title = "Billet #{} : {}".format(instance.pk, instance.title)[:80]
    instance.forum_thread.title = title
    instance.forum_thread.save()
    # Prepare post: url text
    url = SITE_URL + reverse('blog:post', args=[instance.slug])
    url_text = "**{} a posté [un nouveau billet]({}) :**\n".format(
        instance.author, url)
    # Prepare image text
    if instance.image:
        url = "{}/media/{}".format(SITE_URL, str(instance.image))
        image = "![Image]({})\n".format(url)
    # Aggregate
    try:
        content = '\n'.join([url_text, image, instance.content])
    except NameError:
        content = '\n'.join([url_text, instance.content])
    # Create or update Post
    if created:
        author = (ForumUser.objects.get(username=ROBOT_NAME) if ROBOT_NAME
                  else instance.author)
        Post.objects.create(
            author=author,
            thread=instance.forum_thread,
            markup='markdown',
            content_plain=content
        )
    else:
        p = Post.objects.filter(thread=instance.forum_thread).first()
        p.content_plain = content
        p.markup = 'markdown'
        p.save()
