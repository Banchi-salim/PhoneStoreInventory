from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'CustomUser'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='CustomUser/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='CustomUser:login'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html',
        success_url='/accounts/password-change-done/'
    ), name='password_change'),
    path('password-change-done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),
]