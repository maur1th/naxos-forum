from django.urls import path, re_path

from django.contrib.auth import views as auth_views
from . import views
from .forms import CrispyLoginForm, CrispyPasswordResetForm, \
    CrispySetPasswordForm


app_name = 'user'
urlpatterns = [
    path('', views.UpdateUser.as_view(), name='profile'),
    path('password/', views.UpdatePassword, name='password'),
    path('members/', views.MemberList.as_view(), name='members'),
    path('top10/', view=views.Top10.as_view(), name='top10'),
    path('register/', views.Register.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(
         authentication_form=CrispyLoginForm), name='login'),
    path('logout/', auth_views.logout_then_login, name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
            form_class=CrispyPasswordResetForm,
            success_url='user:password_reset_done'),
         name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    re_path((r'reset/(?P<uidb64>[0-9A-Za-z_\-]+)/'
             r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$'),
            auth_views.PasswordResetConfirmView.as_view(
                form_class=CrispySetPasswordForm,
                success_url='user:password_reset_complete'),
            name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
    path('node_api/', views.node_api, name='node_api'),
]
