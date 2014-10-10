from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
    url(
        regex=r'^$',
        view=views.CategoryView.as_view(),
        name='categories'
    ),
    url(
        regex=r'(?P<slug>[\w|\-]+)/$',
        view=views.ThreadView.as_view(),
        name='threads'
    ),
)
