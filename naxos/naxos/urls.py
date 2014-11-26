from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse_lazy

from django.conf import settings


urlpatterns = patterns(
    '',
    url(r'^$', RedirectView.as_view(url=reverse_lazy('forum:top'))),
    url(r'^forum/', include('forum.urls', namespace='forum')),
    url(r'^user/', include('user.urls', namespace='user')),
    url(r'^messages/', include('pm.urls', namespace='pm')),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),

    url(r'^admin/', include(admin.site.urls)),
)
