from django.db import models

from uuslug import uuslug

from forum.util import convert_text_to_html
from user.models import ForumUser

SLUG_LENGTH = 50


class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, verbose_name='Titre')
    author = models.ForeignKey(ForumUser, related_name='blogposts')
    content = models.TextField(verbose_name='Message')
    image = models.ImageField(upload_to="images", blank=True, null=True)
    views = models.IntegerField(default=0)
    slug = models.CharField(max_length=50, unique=True)

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
            this = Post.objects.get(pk=self.pk)
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
