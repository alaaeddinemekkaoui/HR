from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Smart router for /dashboard/
    path('', views.DashboardRouterView.as_view(), name='index'),
    # Explicit dashboards
    path('admin/', views.DashboardView.as_view(), name='admin'),
    path('hr/', views.HRDashboardView.as_view(), name='hr'),
    path('me/', views.UserDashboardView.as_view(), name='user'),
]
