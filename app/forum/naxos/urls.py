from django.urls import include, path
from django.views.generic import RedirectView
from django.urls import reverse_lazy
from django.contrib import admin
from django.views.static import serve

from django.conf import settings


urlpatterns = [
    path('', RedirectView.as_view(url=reverse_lazy('forum:top'),
         permanent=True)),
    path('forum/', include('forum.urls')),
    path('user/', include('user.urls')),
    path('messages/', include('pm.urls')),
    path('blog/', include('blog.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
        path('media/<slug:path>', serve, {
                'document_root': settings.MEDIA_ROOT
        }),
    ]
