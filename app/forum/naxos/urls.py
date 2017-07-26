from django.conf.urls import include, url
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse_lazy
from django.contrib import admin
import django.views.static

from django.conf import settings


urlpatterns = [
    url(r'^$', RedirectView.as_view(url=reverse_lazy('forum:top'),
        permanent=True)),
    url(r'^forum/', include('forum.urls')),
    url(r'^user/', include('user.urls')),
    url(r'^messages/', include('pm.urls')),
    url(r'^blog/', include('blog.urls')),
    url(r'^media/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT}),
    url(r'^admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
