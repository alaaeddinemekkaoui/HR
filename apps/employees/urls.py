from django.urls import path
from .views.employee_views import (
    EmployeeListView,
    EmployeeDetailView,
    EmployeeCreateView,
    EmployeeUpdateView,
    EmployeeDeleteView,
    EmployeeCreateAccountView,
    EmployeeModifyAccountView,
    EmployeeDeleteAccountView,
)
from .views.org_views import (
    DirectionListView, DirectionCreateView, DirectionEditView,
    DivisionListView, DivisionCreateView, DivisionEditView,
    ServiceListView, ServiceCreateView, ServiceEditView,
    DirectionDeleteView, DivisionDeleteView, ServiceDeleteView,
)
from .views.progression_views import (
    RuleListView, RuleCreateView, RuleEditView, RuleDeleteView,
)
from .views.grade_views import (
    GradeListView, GradeCreateView, GradeEditView, GradeDeleteView,
)

app_name = 'employees'

urlpatterns = [
    path('', EmployeeListView.as_view(), name='list'),
    path('create/', EmployeeCreateView.as_view(), name='create'),
    path('<int:pk>/', EmployeeDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', EmployeeUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', EmployeeDeleteView.as_view(), name='delete'),
    path('<int:pk>/create-account/', EmployeeCreateAccountView.as_view(), name='create_account'),
    path('<int:pk>/modify-account/', EmployeeModifyAccountView.as_view(), name='modify_account'),
    path('<int:pk>/delete-account/', EmployeeDeleteAccountView.as_view(), name='delete_account'),
    # Organization management
    path('organization/directions/', DirectionListView.as_view(), name='org_directions'),
    path('organization/directions/create/', DirectionCreateView.as_view(), name='org_direction_create'),
    path('organization/directions/<int:pk>/edit/', DirectionEditView.as_view(), name='org_direction_edit'),
        path('organization/directions/<int:pk>/delete/', DirectionDeleteView.as_view(), name='org_direction_delete'),
    path('organization/divisions/', DivisionListView.as_view(), name='org_divisions'),
    path('organization/divisions/create/', DivisionCreateView.as_view(), name='org_division_create'),
    path('organization/divisions/<int:pk>/edit/', DivisionEditView.as_view(), name='org_division_edit'),
        path('organization/divisions/<int:pk>/delete/', DivisionDeleteView.as_view(), name='org_division_delete'),
    path('organization/services/', ServiceListView.as_view(), name='org_services'),
    path('organization/services/create/', ServiceCreateView.as_view(), name='org_service_create'),
    path('organization/services/<int:pk>/edit/', ServiceEditView.as_view(), name='org_service_edit'),
        path('organization/services/<int:pk>/delete/', ServiceDeleteView.as_view(), name='org_service_delete'),
    # Progression rules
    path('progression/rules/', RuleListView.as_view(), name='rules_list'),
    path('progression/rules/create/', RuleCreateView.as_view(), name='rule_create'),
    path('progression/rules/<int:pk>/edit/', RuleEditView.as_view(), name='rule_edit'),
    path('progression/rules/<int:pk>/delete/', RuleDeleteView.as_view(), name='rule_delete'),
    # Grades management
    path('grades/', GradeListView.as_view(), name='grade_list'),
    path('grades/create/', GradeCreateView.as_view(), name='grade_create'),
    path('grades/<int:pk>/edit/', GradeEditView.as_view(), name='grade_edit'),
    path('grades/<int:pk>/delete/', GradeDeleteView.as_view(), name='grade_delete'),
 ]
