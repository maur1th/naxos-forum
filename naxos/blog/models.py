from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.urlresolvers import reverse

from uuslug import uuslug
from socket import gethostname

from forum.util import convert_text_to_html
from forum.models import Category, Thread, Post, SLUG_LENGTH
from user.models import ForumUser

def import_from(module, name):
    module = __import__(module, fromlist=[name])
    return getattr(module, name)

try:
    import os
    SITE_URL = import_from(
        os.environ.get("DJANGO_SETTINGS_MODULE"), 'SITE_URL')
except:
    SITE_URL = ''


class BlogPost(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=80, verbose_name='Titre')
    author = models.ForeignKey(ForumUser, related_name='blogposts')
    content = models.TextField(verbose_name='Message')
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
        except: pass
        super().save(*args, **kwargs)

    @property
    def html(self):
      return convert_text_to_html(self.content, 'markdown')

    def __str__(self):
        return self.title

    class Meta:
      ordering = ['-pk']


## Model signal handlers ###
@receiver(pre_save, sender=BlogPost)
def new_post_pre_save(instance, **kwargs):
    """Create related thread and post"""
    if instance.pk: return
    c = Category.objects.get(slug='jep')
    title = "empty"  # For now, need post pk first
    t = Thread.objects.create(title=title,
                              author=instance.author,
                              category=c)
    instance.forum_thread = t


@receiver(post_save, sender=BlogPost)
def new_post_post_save(instance, created, **kwargs):
    """Update related thread's title"""
    if not created: return
    title = "Billet #{} : {}".format(instance.pk, instance.title)[:80]
    instance.forum_thread.title = title
    instance.forum_thread.save()
    url = SITE_URL + reverse('blog:post', args=[instance.pk])
    Post.objects.create(author=instance.author,
                        thread=instance.forum_thread,
                        content_plain="[url={}]Billet[/url]".format(url))
