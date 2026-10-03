from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.home, name='home'),
    path('video/', views.video_analysis, name='video_analysis'),
    path('channel/', views.channel_analysis, name='channel_analysis'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('history/', views.history, name='history'),
    path('video/<str:video_id>/', views.video_detail, name='video_detail'),
    path('channel/<str:channel_id>/', views.channel_detail, name='channel_detail'),
]