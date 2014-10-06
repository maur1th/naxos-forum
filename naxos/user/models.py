from django.db import models
from django.contrib.auth.models import User


class UserSettings(models.Model):
    user = models.OneToOneField(User)
    emailVisible = models.BooleanField(default=False)
    subscribeToMails = models.BooleanField(default=True)
    mpPopupNotif = models.BooleanField(default=True)
    mpEmailNotif = models.BooleanField(default=False)
    avatar = models.ImageField()
    quote = models.CharField(max_length=50)
    website = models.URLField()

    def __str__(self):
        return self.user.username
