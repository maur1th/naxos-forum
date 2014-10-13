from django.conf.urls import patterns, url

from . import views

# TODO
# Prevent posts called 'new' from being created

urlpatterns = patterns('',
    url(
        regex=r'^$',
        view=views.TopView.as_view(),
        name='top'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+?)/$',
        view=views.ThreadView.as_view(),
        name='category'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+?)/(?P<thread_slug>[\w|\-]+?)/$',
        view=views.PostView.as_view(),
        name='thread'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+)/new/$',
        view=views.NewThread.as_view(),
        name='new_thread'
    ),
)
