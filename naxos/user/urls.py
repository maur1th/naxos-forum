from django.conf.urls import url

import django.contrib.auth.views
from . import views
from .forms import CrispyLoginForm, CrispyPasswordResetForm, \
    CrispySetPasswordForm


app_name = 'user'
urlpatterns = [
    url(
        regex=r'^$',
        view=views.UpdateUser.as_view(),
        name='profile'
    ),
    url(
        regex=r'^password/$',
        view=views.UpdatePassword,
        name='password'
    ),
    url(
        regex=r'^members/$',
        view=views.MemberList.as_view(),
        name='members'
    ),
    url(
        regex=r'^top10/$',
        view=views.Top10.as_view(),
        name='top10'
    ),
    url(
        regex=r'^register/$',
        view=views.Register.as_view(),
        name='register'
    ),
    url(
        regex=r'^login/$',
        view=django.contrib.auth.views.login,
        kwargs={'authentication_form': CrispyLoginForm},
        name='login'
    ),
    url(
        regex=r'^logout/$',
        view=django.contrib.auth.views.logout_then_login,
        kwargs={'login_url': 'user:login'},
        name='logout'
    ),
    url(
        regex=r'^password_reset/$',
        view=django.contrib.auth.views.password_reset,
        kwargs={'password_reset_form': CrispyPasswordResetForm,
                'post_reset_redirect': 'user:password_reset_done'},
        name='password_reset'
    ),
    url(
        regex=r'^password_reset/done/$',
        view=django.contrib.auth.views.password_reset_done,
        name='password_reset_done'
    ),
    url(
        regex=r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        view=django.contrib.auth.views.password_reset_confirm,
        kwargs={'set_password_form': CrispySetPasswordForm,
                'post_reset_redirect': 'user:password_reset_complete'},
        name='password_reset_confirm'
    ),
    url(
        regex=r'^reset/done/$',
        view=django.contrib.auth.views.password_reset_complete,
        name='password_reset_complete'
    ),
    url(
        regex=r'^node_api/$',
        view=views.node_api,
        name='node_api'
    ),
]
