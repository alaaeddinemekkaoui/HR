from django.urls import path
from . import views

app_name = 'leaves'

urlpatterns = [
    path('types/', views.LeaveTypeListView.as_view(), name='types'),
    path('types/create/', views.LeaveTypeCreateView.as_view(), name='type_create'),
    path('types/<int:pk>/edit/', views.LeaveTypeEditView.as_view(), name='type_edit'),

    path('my/', views.MyLeavesView.as_view(), name='my'),
    path('request/', views.LeaveRequestCreateView.as_view(), name='request'),
    path('request/<int:pk>/delete/', views.LeaveRequestDeleteView.as_view(), name='request_delete'),

    path('approve/', views.LeaveApproveListView.as_view(), name='approve'),
    path('approve/<int:pk>/', views.LeaveApproveActionView.as_view(), name='approve_action'),
]
