from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import m2m_changed
from django.core.cache import cache

from forum.util import keygen


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
    logo = models.ImageField(upload_to="logo",
                             blank=True)
    quote = models.CharField(max_length=50,
                             blank=True,
                             verbose_name='Citation')
    website = models.URLField(blank=True,
                              verbose_name='Site web')
    postsReadCaret = models.ManyToManyField('forum.Post', blank=True)
    pmReadCaret = models.ManyToManyField('pm.Message', blank=True)
    pmUnreadCount = models.IntegerField(default=0)

    class Meta:
        ordering = ["pk"]


class TokenPool(models.Model):
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
def postsReadCaret_changed(sender, action, instance, **kwargs):
    """Updates cached data each time a post is added to postsReadCaret"""
    if action == "post_add":
        cache.set("{:d}/readCaret".format(instance.pk),
                  instance.postsReadCaret.all(),
                  None)

m2m_changed.connect(postsReadCaret_changed,
    sender=ForumUser.postsReadCaret.through)
