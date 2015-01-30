from django.db import models
from uuslug import uuslug

from user.models import ForumUser

SLUG_LENGTH = 50


class Post(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100)
    author = models.ForeignKey(ForumUser, related_name='blogposts')
    content = models.TextField()
    image = models.ImageField(upload_to="images", blank=True, null=True)
    views = models.IntegerField(default=0)
    slug = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        self.slug = uuslug(self.title,
                           instance=self,
                           max_length=SLUG_LENGTH)
        if not self.slug:  # Prevent empty strings as slug
            self.slug = uuslug('sans titre',
                               instance=self,
                               max_length=SLUG_LENGTH)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
      ordering = ['-pk']
