"""
JWT Authentication URLs
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .jwt_views import (
    CustomTokenObtainPairView,
    register_user,
    logout_user,
    get_current_user,
    change_password,
)

app_name = 'jwt_auth'

urlpatterns = [
    # Token management
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User management
    path('register/', register_user, name='register'),
    path('logout/', logout_user, name='logout'),
    path('me/', get_current_user, name='current_user'),
    path('change-password/', change_password, name='change_password'),
]
