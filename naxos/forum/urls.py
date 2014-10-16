from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
    url(
        regex=r'^$',
        view=views.TopView.as_view(),
        name='top'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+)/$',
        view=views.ThreadView.as_view(),
        name='category'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+)/\+$',
        view=views.NewThread.as_view(),
        name='new_thread'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+)/(?P<thread_slug>[\w|\-]+)/$',
        view=views.PostView.as_view(),
        name='thread'
    ),
)
