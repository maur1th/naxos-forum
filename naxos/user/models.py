from django.db import models
from django.contrib.auth.models import AbstractUser


class ForumUser(AbstractUser):
    """Custom user model"""
    emailVisible = models.BooleanField(default=False)
    subscribeToEmails = models.BooleanField(default=True)
    mpPopupNotif = models.BooleanField(default=True)
    mpEmailNotif = models.BooleanField(default=False)
    logo = models.ImageField(upload_to="logo",
                             blank=True)
    quote = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
