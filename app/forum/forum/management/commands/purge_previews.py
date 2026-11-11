from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from forum.models import Preview


class Command(BaseCommand):
    help = "Delete post previews older than one day."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=1)
        deleted, _ = Preview.objects.filter(created__lt=cutoff).delete()
        self.stdout.write("Deleted {} preview(s).".format(deleted))
