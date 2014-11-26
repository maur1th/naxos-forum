from django.db import models
from django.contrib.auth.models import AbstractUser


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
    logo = models.ImageField(upload_to="logo",
                             blank=True)
    quote = models.CharField(max_length=50,
                             blank=True,
                             verbose_name='Citation')
    website = models.URLField(blank=True,
                              verbose_name='Site web')
    postsReadCaret = models.ManyToManyField('forum.Post', blank=True)

    class Meta:
        ordering = ["username"]
