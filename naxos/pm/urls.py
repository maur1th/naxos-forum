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
        regex=r'^(?P<pk>[0-9]+)/$',
        view=views.MessageView.as_view(),
        name='msg'
    ),
    url(
        regex=r'^\+$',
        view=views.NewConversation.as_view(),
        name='new_conv'
    ),
    url(
        regex=r'^(?P<pk>[0-9]+)/\+$',
        view=views.NewMessage,
        name='new_msg'
    ),
    url(
        regex=r'^delete_msg/(?P<pk>[0-9]+)$',
        view=views.DeleteMessage.as_view(),
        name='delete_msg'
    ),
    url(
        regex=r'^\$$',
        view=views.GetConversation,
        name='search'
    ),
)
