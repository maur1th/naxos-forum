from django.db import models
from django.contrib.auth.models import User


class UserSettings(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    emailVisible = models.BooleanField(default=False)
    subscribeToMails = models.BooleanField(default=True)
    mpPopupNotif = models.BooleanField(default=True)
    mpEmailNotif = models.BooleanField(default=False)
    avatar = models.ImageField(blank=True)
    quote = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.user.username
