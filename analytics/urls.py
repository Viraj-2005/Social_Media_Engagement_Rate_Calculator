from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.home, name='home'),
    path('video/', views.video_analysis, name='video_analysis'),
    path('channel/', views.channel_analysis, name='channel_analysis'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/videos/', views.video_dashboard, name='video_dashboard'),
    path('dashboard/channels/', views.channel_dashboard, name='channel_dashboard'),
    path('history/', views.history, name='history'),
    path('video/<str:video_id>/', views.video_detail, name='video_detail'),
    path('channel/<str:channel_id>/', views.channel_detail, name='channel_detail'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
        authentication_form=views.SignInForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='analytics:home'
    ), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        form_class=views.PasswordResetForm,
        success_url='/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/password-reset/complete/'
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]