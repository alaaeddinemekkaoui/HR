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
# Import async views for API endpoints (high performance under load)
from .views.async_views import (
    AsyncGetDivisionsAPIView,
    AsyncGetServicesAPIView,
)
from .views.org_views import (
    DirectionListView, DirectionCreateView, DirectionEditView,
    DivisionListView, DivisionCreateView, DivisionEditView,
    ServiceListView, ServiceCreateView, ServiceEditView,
    DirectionDeleteView, DivisionDeleteView, ServiceDeleteView,
    DepartementListView, DepartementCreateView, DepartementEditView, DepartementDeleteView,
    FiliereListView, FiliereCreateView, FiliereEditView, FiliereDeleteView,
)
from .views.progression_views import (
    RuleListView, RuleCreateView, RuleEditView, RuleDeleteView,
)
from .views.grade_views import (
    GradeListView, GradeCreateView, GradeEditView, GradeDeleteView,
)
from .views.history_views import (
    EmploymentHistoryListView,
    EmploymentHistoryCreateView,
    EmploymentHistoryUpdateView,
    EmploymentHistoryDeleteView,
    GradeChangeCreateView,
    ContractCreateView,
    RetirementCreateView,
)
from .views.deployment_views import (
    DeploymentListView,
    DeploymentForfaitaireCreateView,
    DeploymentRealCreateView,
    OrdreMissionCreateView,
    OrdreMissionApprovalListView,
    OrdreMissionReviewView,
    GradeDeploymentRateListView,
    GradeDeploymentRateCreateView,
    GradeDeploymentRateUpdateView,
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
    # API endpoints - using async views for high performance under load
    path('api/get-divisions/', AsyncGetDivisionsAPIView.as_view(), name='api_get_divisions'),
    path('api/get-services/', AsyncGetServicesAPIView.as_view(), name='api_get_services'),
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
    # Département management
    path('organization/departements/', DepartementListView.as_view(), name='org_departements'),
    path('organization/departements/create/', DepartementCreateView.as_view(), name='org_departement_create'),
    path('organization/departements/<int:pk>/edit/', DepartementEditView.as_view(), name='org_departement_edit'),
    path('organization/departements/<int:pk>/delete/', DepartementDeleteView.as_view(), name='org_departement_delete'),
    # Filière management
    path('organization/filieres/', FiliereListView.as_view(), name='org_filieres'),
    path('organization/filieres/create/', FiliereCreateView.as_view(), name='org_filiere_create'),
    path('organization/filieres/<int:pk>/edit/', FiliereEditView.as_view(), name='org_filiere_edit'),
    path('organization/filieres/<int:pk>/delete/', FiliereDeleteView.as_view(), name='org_filiere_delete'),
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
    # Employment history
    path('<int:employee_id>/history/', EmploymentHistoryListView.as_view(), name='history_list'),
    path('<int:employee_id>/history/add/', EmploymentHistoryCreateView.as_view(), name='history_create'),
    path('history/<int:pk>/edit/', EmploymentHistoryUpdateView.as_view(), name='history_edit'),
    path('history/<int:pk>/delete/', EmploymentHistoryDeleteView.as_view(), name='history_delete'),
    path('<int:employee_id>/history/grade-change/', GradeChangeCreateView.as_view(), name='grade_change'),
    path('<int:employee_id>/history/contract/', ContractCreateView.as_view(), name='contract_create'),
    path('<int:employee_id>/history/retirement/', RetirementCreateView.as_view(), name='retirement_create'),
    # Deployments (Déplacements)
    path('deployments/', DeploymentListView.as_view(), name='deployments_list'),
    path('deployments/forfaitaire/create/', DeploymentForfaitaireCreateView.as_view(), name='deployment_forfaitaire_create'),
    path('deployments/real/create/', DeploymentRealCreateView.as_view(), name='deployment_real_create'),
    path('deployments/ordre-mission/create/', OrdreMissionCreateView.as_view(), name='ordre_mission_create'),
    path('deployments/approval/', OrdreMissionApprovalListView.as_view(), name='deployments_approval'),
    path('deployments/ordre-mission/<int:pk>/review/', OrdreMissionReviewView.as_view(), name='ordre_mission_review'),
    path('deployments/rates/', GradeDeploymentRateListView.as_view(), name='deployment_rates'),
    path('deployments/rates/create/', GradeDeploymentRateCreateView.as_view(), name='deployment_rate_create'),
    path('deployments/rates/<int:pk>/edit/', GradeDeploymentRateUpdateView.as_view(), name='deployment_rate_edit'),
 ]
