from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='admin_dashboard:index', permanent=False)),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # API Authentication (JWT) - no namespace needed, jwt_urls defines it
    path('api/auth/', include('apps.authentication.jwt_urls')),
    
    # App URLs
    path('employees/', include('apps.employees.urls', namespace='employees')),
    path('auth/', include('apps.authentication.urls', namespace='authentication')),
    path('dashboard/', include('apps.admin_dashboard.urls', namespace='admin_dashboard')),
    path('roles/', include('apps.roles.urls', namespace='roles')),
    path('leaves/', include('apps.leaves.urls', namespace='leaves')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('documents/', include('apps.documents.urls', namespace='documents')),
    path('signatures/', include('apps.signatures.urls', namespace='signatures')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
