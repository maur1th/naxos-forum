from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
    url(
        regex=r'^register/$',
        view=views.Register.as_view(),
        name='register'
    ),
)
