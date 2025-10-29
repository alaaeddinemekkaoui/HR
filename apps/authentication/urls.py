from django.urls import path, include
from . import views

app_name = 'authentication'

urlpatterns = [
    # Session-based authentication (web UI)
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('account/', views.AccountSettingsView.as_view(), name='account'),
    path('upload-picture/', views.UploadProfilePictureView.as_view(), name='upload_picture'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('users/', views.UserListView.as_view(), name='users'),
    # Device-based login endpoint (optional passwordless)
    path('device-login/', views.device_login_api, name='device_login_api'),
    
    # JWT API authentication (delegated to jwt_urls.py)
    # Accessible via /auth/jwt/* (will map to jwt_urls)
    path('jwt/', include('apps.authentication.jwt_urls')),
]
