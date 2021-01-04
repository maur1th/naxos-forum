from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from django.conf import settings

@login_required
def get_version(request):
    return HttpResponse(settings.VERSION)
