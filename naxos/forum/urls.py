from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
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
        regex=r'^(?P<category_slug>[\w|\-]+)/(?P<thread_slug>[\w|\-]+)/$',
        view=views.PostView.as_view(),
        name='thread'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+)/\+$',
        view=views.NewThread.as_view(),
        name='new_thread'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+)/\+poll$',
        view=views.NewPoll,
        name='new_poll'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+)/(?P<thread_slug>[\w|\-]+)/vote/$',
        view=views.VotePoll,
        name='vote'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+)/(?P<thread_slug>[\w|\-]+)/\+$',
        view=views.NewPost.as_view(),
        name='new_post'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+)/(?P<thread_slug>[\w|\-]+)/edit=(?P<pk>\d+)$',
        view=views.EditPost.as_view(),
        name='edit'
    ),
    url(
        regex=r'^(?P<category_slug>[\w|\-]+)/(?P<thread_slug>[\w|\-]+)/quote=(?P<pk>\d+)$',
        view=views.QuotePost.as_view(),
        name='quote'
    ),
    url(
        regex=r'^preview/(?P<pk>[0-9]+)$',
        view=views.PreviewView.as_view(),
        name='preview'
    ),
    url(
        regex=(r'^(?P<category_slug>[\w|\-]+)/'
                '(?P<thread_slug>[\w|\-]+)/cession$'),
        view=views.ThreadCessionView.as_view(),
        name='cession'
    ),
)
