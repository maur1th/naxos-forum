from django.urls import path, re_path

from . import views


app_name = 'pm'
urlpatterns = [
    path('', views.PMTopView.as_view(), name='top'),
    path('<int:pk>/', views.MessageView.as_view(), name='msg'),
    path('+', views.NewConversation.as_view(), name='new_conv'),
    path('+/<int:recipient>/', views.NewConversation.as_view(),
         name='new_conv'),
    path('<int:pk>/+', views.NewMessage, name='new_msg'),
    path('<int:pk>/switch_status', views.SwitchConversationStatus.as_view(),
         name='switch_status'),
    path('delete_msg/<int:pk>', views.DeleteMessage.as_view(),
         name='delete_msg'),
    re_path(r'^\$$', views.GetConversation, name='search'),
]
