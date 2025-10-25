from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='employees:list', permanent=False)),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('employees/', include('apps.employees.urls', namespace='employees')),
    path('auth/', include('apps.authentication.urls', namespace='authentication')),
    path('dashboard/', include('apps.admin_dashboard.urls', namespace='admin_dashboard')),
    path('roles/', include('apps.roles.urls', namespace='roles')),
    path('leaves/', include('apps.leaves.urls', namespace='leaves')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('documents/', include('apps.documents.urls', namespace='documents')),
]
