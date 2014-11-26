from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns(
    '',
    url(
        regex=r'^$',
        view=views.PMTopView.as_view(),
        name='top'
    ),
    url(
        regex=r'^\+$',
        view=views.NewConversation.as_view(),
        name='new'
    )
)
