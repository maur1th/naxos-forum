from django.urls import path

from . import views


app_name = 'blog'
urlpatterns = [
    path('', views.TopView.as_view(), name='top'),
    path('<slug:slug>', views.PostView.as_view(), name='post'),
    path('+', views.NewPost.as_view(), name='new_post'),
    path('edit=<slug:slug>', views.EditPost.as_view(), name='edit'),
]
