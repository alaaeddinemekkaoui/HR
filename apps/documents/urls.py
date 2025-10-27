from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.DocumentsHomeView.as_view(), name='home'),
    # Admin document generator
    path('admin-generator/', views.AdminDocumentGeneratorView.as_view(), name='admin_generator'),
    # Static documents
    path('attestation-travail/<int:employee_id>/', views.AttestationTravailView.as_view(), name='attestation_travail'),
    path('decision-conge/<int:leave_id>/', views.DecisionCongeView.as_view(), name='decision_conge'),
    path('attestation-salaire/<int:employee_id>/', views.AttestationSalaireView.as_view(), name='attestation_salaire'),
    # PDF downloads
    path('attestation-travail/<int:employee_id>/pdf/', views.AttestationTravailPDFView.as_view(), name='attestation_travail_pdf'),
    path('decision-conge/<int:leave_id>/pdf/', views.DecisionCongePDFView.as_view(), name='decision_conge_pdf'),
    path('attestation-salaire/<int:employee_id>/pdf/', views.AttestationSalairePDFView.as_view(), name='attestation_salaire_pdf'),
    # Dynamic templates (HR)
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    path('templates/create/', views.TemplateCreateView.as_view(), name='template_create'),
    path('templates/<int:pk>/edit/', views.TemplateEditView.as_view(), name='template_edit'),
    path('templates/<int:pk>/delete/', views.TemplateDeleteView.as_view(), name='template_delete'),
    path('template/<slug:slug>/', views.TemplateRenderView.as_view(), name='template_render'),
    path('template/<slug:slug>/<int:employee_id>/', views.TemplateRenderView.as_view(), name='template_render_for'),
]
