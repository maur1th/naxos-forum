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


class BlogPost(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=80, verbose_name='Titre')
    author = models.ForeignKey(
        ForumUser,
        related_name='blogposts',
        on_delete=models.CASCADE)
    content = models.TextField(verbose_name='Message',
                               max_length=100000)
    image = models.ImageField(upload_to="images", blank=True, null=True)
    views = models.IntegerField(default=0)
    slug = models.CharField(max_length=SLUG_LENGTH, unique=True)
    forum_thread = models.OneToOneField(
        Thread,
        null=True,
        related_name='blog_post',
        on_delete=models.CASCADE)

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
