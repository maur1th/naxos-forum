from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import RedirectView
from django.core.urlresolvers import reverse_lazy

urlpatterns = patterns('',
    url(r'^$', RedirectView.as_view(url=reverse_lazy('forum:welcome'))),
    url(r'^forum/', include('forum.urls', namespace='forum')),
    url(r'^user/', include('user.urls', namespace='user')),
    
    url(r'^admin/', include(admin.site.urls)),
)
