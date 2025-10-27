from django.urls import path
from .views import NotificationListView, NotificationMarkAllReadView, NotificationClearAllView, NotificationGoView

app_name = 'notifications'
urlpatterns = [
    path('', NotificationListView.as_view(), name='list'),
    path('mark-all-read/', NotificationMarkAllReadView.as_view(), name='mark_all_read'),
    path('clear-all/', NotificationClearAllView.as_view(), name='clear_all'),
    path('<int:pk>/go/', NotificationGoView.as_view(), name='go'),
]
