from django.conf.urls import include, url
from django.views.generic import RedirectView
import django.views.static
from django.core.urlresolvers import reverse_lazy

from django.conf import settings


urlpatterns = [
    url(r'^$', RedirectView.as_view(url=reverse_lazy('forum:top'),
        permanent=True)),
    url(r'^forum/', include('forum.urls', namespace='forum')),
    url(r'^user/', include('user.urls', namespace='user')),
    url(r'^messages/', include('pm.urls', namespace='pm')),
    url(r'^blog/', include('blog.urls', namespace='blog')),
    url(r'^media/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT}),
]
