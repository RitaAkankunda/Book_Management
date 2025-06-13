from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

app_name = 'users'

urlpatterns = [    # Authentication endpoints
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # User management endpoints (admin only)
    path('', views.UserListView.as_view(), name='user_list'),  # List all users
    
    # Profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='profile'),  # Own profile
    path('profile/<int:user_id>/', views.UserProfileView.as_view(), name='user_profile'),  # Other user's profile (admin)
    
    # Password management
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/<str:uidb64>/<str:token>/', 
         views.PasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
]
