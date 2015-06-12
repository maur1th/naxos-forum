from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.core.cache import cache

from forum.util import keygen

from datetime import datetime


FORUM_INIT = datetime(2013,1,1)

### Model classes ###
class ForumUser(AbstractUser):

    """Custom user model"""
    emailVisible = models.BooleanField(
        default=False,
        verbose_name='E-mail visible')
    subscribeToEmails = models.BooleanField(
        default=True,
        verbose_name='Mailing-list')
    mpEmailNotif = models.BooleanField(
        default=False,
        verbose_name='Notification des MP par e-mail')
    showSmileys = models.BooleanField(
        default=False,
        verbose_name='Affichage des smileys par defaut')
    fullscreen = models.BooleanField(
        default=False,
        verbose_name='Utilisation de la largeur de l\'écran')
    showLogosOnSmartphone = models.BooleanField(default=True, verbose_name='Afficher les logos sur smartphone')
    logo = models.ImageField(upload_to="logo",
                             blank=True)
    quote = models.CharField(max_length=50,
                             blank=True,
                             verbose_name='Citation')
    website = models.URLField(blank=True,
                              verbose_name='Site web')
    pmReadCaret = models.ManyToManyField('pm.Message', blank=True)
    pmUnreadCount = models.IntegerField(default=0)
    resetDateTime = models.DateTimeField(default=FORUM_INIT)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["pk"]

    def save(self, *args, **kwargs):
        # Delete old logo
        try:
            this = ForumUser.objects.get(pk=self.pk)
            if this.logo != self.logo:
                this.logo.delete()
        except: pass
        super().save(*args, **kwargs)


class Bookmark(models.Model):
    user = models.ForeignKey(ForumUser, related_name='bookmarks')
    thread = models.ForeignKey('forum.Thread', related_name='bookmarks')
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'thread')
        index_together = ('user', 'thread')
        get_latest_by = 'timestamp'

    def __str__(self):
        return "{} {} {}".format(self.user, self.thread, self.timestamp)


class TokenPool(models.Model):
    "Contains tokens for user creation"
    token = models.CharField(unique=True, max_length=50)

    def save(self, *args, **kwargs):
        queryset = self.__class__.objects.all()
        self.token = keygen()
        while queryset.filter(token=self.token).exists():
            self.token = keygen()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.token


### Model signal handlers ###
@receiver(post_save, sender=ForumUser)
def update_user_cache(instance, **kwargs):
    cache.set('user/{}'.format(instance.pk), instance, None)
