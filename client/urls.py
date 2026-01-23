from django.urls import path

from . import views

urlpatterns = [

    path('', views.landing, name='landing'),
    path('login/', views.login_user, name='login-v2'),
    path('register/', views.register, name='register-v2'),
    path('profile-setting/', views.profileSetting, name='profile-setting-v2'),
    path('dashboard/', views.dashboard, name='dashboard-v2'),
    path('chat/<str:chatId>/', views.chat, name='chat-v2'),
    path('open-chat/<int:user_id>/', views.openChat, name='openChat-v2'),
    path('new-chat/', views.newChat, name='newChat-v2'),
    path('new-group/', views.newGroup, name='newGroup-v2'),
    path('create-group/', views.createGroup, name='createGroup-v2'),
    path('new-group-profile/', views.newGroupProfile, name='newGroupProfile-v2'),
    path('logout/', views.logout, name='logout-v2'),

]
