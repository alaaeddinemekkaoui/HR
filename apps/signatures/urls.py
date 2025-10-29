from django.urls import path
from . import views
from . import biometric_views

app_name = 'signatures'

urlpatterns = [
    # Signature request views
    path('sign/<int:signature_id>/', views.signature_request_view, name='sign_document'),
    path('reject/<int:signature_id>/', views.reject_signature_view, name='reject_signature'),
    path('detail/<int:signature_id>/', views.signature_detail_view, name='signature_detail'),
    
    # My signature requests
    path('my-requests/', views.my_signature_requests_view, name='my_requests'),
    
    # Document signatures
    path('document/<int:content_type_id>/<int:object_id>/', views.document_signatures_view, name='document_signatures'),
    
    # Admin dashboard (IT Admin only)
    path('admin/dashboard/', views.admin_signatures_dashboard, name='admin_dashboard'),
    path('admin/verify-device/<int:device_id>/', views.admin_verify_device, name='admin_verify_device'),
    path('admin/deactivate-device/<int:device_id>/', views.admin_deactivate_device, name='admin_deactivate_device'),
    # Admin: stamp artifacts
    path('admin/artifacts/', views.admin_stamp_artifacts_view, name='admin_artifacts'),
    path('admin/artifacts/approve/<int:artifact_id>/', views.admin_approve_artifact_view, name='admin_approve_artifact'),
    
    # Biometric device management
    path('devices/', biometric_views.my_biometric_devices_view, name='my_devices'),
    path('devices/register/', biometric_views.register_biometric_device_view, name='register_device'),
    path('devices/deactivate/<int:device_id>/', biometric_views.deactivate_device_view, name='deactivate_device'),
    # Encrypted stamp artifact upload
    path('artifacts/upload/', views.upload_stamp_artifact_view, name='upload_artifact'),
    
    # API endpoints
    path('api/verify/<int:signature_id>/', views.verify_signature_api, name='verify_signature_api'),
    path('api/detect-usb/', biometric_views.detect_usb_signature_device_api, name='detect_usb_api'),
    path('api/verify-fingerprint/', biometric_views.verify_fingerprint_api, name='verify_fingerprint_api'),
    path('api/sign-usb/', biometric_views.sign_with_usb_device_api, name='sign_usb_api'),
    path('api/sign-biometric/', biometric_views.sign_with_biometric_api, name='sign_biometric_api'),
    path('api/sign-usb-stamp/', biometric_views.sign_with_usb_stamp_api, name='sign_usb_stamp_api'),
    path('api/verify-stamp-password/', biometric_views.verify_usb_stamp_password_api, name='verify_stamp_password_api'),
]
