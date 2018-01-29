from django.urls import path

from . import views


app_name = 'forum'
urlpatterns = [
    path('', views.CategoryView.as_view(), name='top'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('<slug:category_slug>/', views.ThreadView.as_view(),
         name='category'),
    path('<slug:category_slug>/<slug:thread_slug>/',
         views.PostView.as_view(), name='thread'),
    path('post/<int:pk>', views.PostDetailView.as_view(), name='post'),
    path('<slug:category_slug>/+', views.NewThread.as_view(),
         name='new_thread'),
    path('<slug:category_slug>/+poll', views.NewPoll, name='new_poll'),
    path('<slug:category_slug>/<slug:thread_slug>/vote/', views.VotePoll,
         name='vote'),
    path('<slug:category_slug>/<slug:thread_slug>/+', views.NewPost.as_view(),
         name='new_post'),
    path('<slug:category_slug>/<slug:thread_slug>/edit=<int:pk>',
         views.EditPost.as_view(), name='edit'),
    path('<slug:category_slug>/<slug:thread_slug>/quote=<int:pk>',
         views.QuotePost.as_view(), name='quote'),
    path('reset_bookmarks/<int:pk>', views.ResetBookmarks.as_view(),
         name='reset_bookmarks'),
    path('delete_thread/<int:pk>', views.DeleteThread.as_view(),
         name='delete_thread'),
    path('preview/<int:pk>', views.PreviewView.as_view(), name='preview'),
]
