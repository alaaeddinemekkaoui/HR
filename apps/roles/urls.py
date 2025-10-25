from django.urls import path
from . import views

app_name = 'roles'

urlpatterns = [
    path('', views.RolesInfoView.as_view(), name='index'),
    path('groups/', views.GroupListView.as_view(), name='groups'),
    path('groups/<int:group_id>/edit/', views.GroupEditView.as_view(), name='group_edit'),
    path('groups/create/', views.GroupCreateView.as_view(), name='group_create'),
    path('groups/<int:group_id>/delete/', views.GroupDeleteView.as_view(), name='group_delete'),
    path('users/', views.UserListView.as_view(), name='users'),
    path('users/<int:user_id>/roles/', views.UserRoleEditView.as_view(), name='user_roles'),
    path('users/<int:user_id>/custom-role/', views.UserCustomRoleCreateView.as_view(), name='user_custom_role'),
    path('users/<int:user_id>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    
    # New: Role and function management
    path('roles/', views.RoleListView.as_view(), name='role_list'),
    path('roles/create/', views.RoleCreateView.as_view(), name='role_create'),
    path('roles/create-with-permissions/', views.RoleCreateWithPermissionsView.as_view(), name='role_create_with_permissions'),
    path('roles/<int:role_id>/edit/', views.RoleEditView.as_view(), name='role_edit'),
    path('roles/<int:role_id>/permissions/', views.RolePermissionsView.as_view(), name='role_permissions'),
    path('functions/', views.FunctionListView.as_view(), name='function_list'),
]
