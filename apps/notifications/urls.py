from django.urls import path
from .views import NotificationListView, NotificationMarkAllReadView, NotificationGoView

app_name = 'notifications'
urlpatterns = [
    path('', NotificationListView.as_view(), name='list'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='mark_all_read'),
    path('<int:pk>/go/', NotificationGoView.as_view(), name='go'),
]
