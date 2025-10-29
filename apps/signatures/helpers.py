"""
Helper functions to integrate electronic signatures into existing HR workflows.
Import these functions in your views to add signature functionality.
"""

from django.contrib.contenttypes.models import ContentType
from apps.signatures.models import ElectronicSignature, SignatureStatus, SignatureType
from apps.signatures.utils import create_signature_request


def add_deployment_signatures(deployment):
    """
    Automatically create signature requests when a deployment is created.
    
    Usage in views:
        deployment = form.save()
        add_deployment_signatures(deployment)
    """
    from apps.roles.models import Role, RoleAssignment
    
    signatures_created = []
    
    # 1. Employee signature
    if deployment.employee and deployment.employee.user:
        sig = create_signature_request(
            document=deployment,
            signer=deployment.employee.user,
            signature_type=SignatureType.EMPLOYEE,
            expiry_days=7
        )
        signatures_created.append(sig)
    
    # 2. Manager/Supervisor signature (if exists)
    # Assuming manager field exists on Employee model
    if hasattr(deployment.employee, 'manager') and deployment.employee.manager:
        sig = create_signature_request(
            document=deployment,
            signer=deployment.employee.manager.user,
            signature_type=SignatureType.MANAGER,
            expiry_days=7
        )
        signatures_created.append(sig)
    
    # 3. HR Admin signature
    # Find users with HR Admin role
    hr_admins = RoleAssignment.objects.filter(
        role__name='HR Admin'
    ).select_related('user').first()
    
    if hr_admins:
        sig = create_signature_request(
            document=deployment,
            signer=hr_admins.user,
            signature_type=SignatureType.HR_ADMIN,
            expiry_days=14
        )
        signatures_created.append(sig)
    
    # 4. Director signature (for higher-level approvals)
    # Add logic to determine director based on your org structure
    
    return signatures_created


def add_leave_request_signatures(leave_request):
    """
    Automatically create signature requests when a leave request is submitted.
    
    Usage in views:
        leave_request = form.save()
        add_leave_request_signatures(leave_request)
    """
    from apps.roles.models import RoleAssignment
    
    signatures_created = []
    
    # 1. Employee signature (confirming the request)
    if leave_request.employee and leave_request.employee.user:
        sig = create_signature_request(
            document=leave_request,
            signer=leave_request.employee.user,
            signature_type=SignatureType.EMPLOYEE,
            expiry_days=3
        )
        signatures_created.append(sig)
    
    # 2. Manager signature (approver)
    if hasattr(leave_request.employee, 'manager') and leave_request.employee.manager:
        sig = create_signature_request(
            document=leave_request,
            signer=leave_request.employee.manager.user,
            signature_type=SignatureType.MANAGER,
            expiry_days=7
        )
        signatures_created.append(sig)
    
    # 3. HR Admin signature (for final approval)
    hr_admin = RoleAssignment.objects.filter(
        role__name='HR Admin'
    ).select_related('user').first()
    
    if hr_admin:
        sig = create_signature_request(
            document=leave_request,
            signer=hr_admin.user,
            signature_type=SignatureType.HR_ADMIN,
            expiry_days=14
        )
        signatures_created.append(sig)
    
    return signatures_created


def add_document_signatures(document, signers_list):
    """
    Generic function to add signatures to any document.
    
    Args:
        document: The document object (Deployment, LeaveRequest, etc.)
        signers_list: List of dicts with 'user' and 'signature_type'
    
    Example:
        signers = [
            {'user': employee_user, 'signature_type': SignatureType.EMPLOYEE},
            {'user': manager_user, 'signature_type': SignatureType.MANAGER},
            {'user': hr_user, 'signature_type': SignatureType.HR_ADMIN},
        ]
        add_document_signatures(deployment, signers)
    """
    signatures_created = []
    
    for signer_info in signers_list:
        sig = create_signature_request(
            document=document,
            signer=signer_info['user'],
            signature_type=signer_info.get('signature_type', SignatureType.EMPLOYEE),
            expiry_days=signer_info.get('expiry_days', 7)
        )
        signatures_created.append(sig)
    
    return signatures_created


def get_document_signatures(document):
    """
    Get all signatures for a specific document.
    
    Usage:
        signatures = get_document_signatures(deployment)
        for sig in signatures:
            print(f"{sig.signer.username}: {sig.status}")
    """
    content_type = ContentType.objects.get_for_model(document)
    
    return ElectronicSignature.objects.filter(
        content_type=content_type,
        object_id=document.id
    ).select_related('signer').order_by('created_at')


def is_document_fully_signed(document):
    """
    Check if all signatures for a document are completed.
    
    Usage:
        if is_document_fully_signed(deployment):
            deployment.status = 'approved'
            deployment.save()
    """
    signatures = get_document_signatures(document)
    
    if not signatures.exists():
        return False
    
    return all(sig.status == SignatureStatus.SIGNED for sig in signatures)


def get_pending_signature_for_user(document, user):
    """
    Get the pending signature request for a specific user and document.
    
    Usage in template context:
        context['user_pending_signature'] = get_pending_signature_for_user(deployment, request.user)
    """
    content_type = ContentType.objects.get_for_model(document)
    
    return ElectronicSignature.objects.filter(
        content_type=content_type,
        object_id=document.id,
        signer=user,
        status=SignatureStatus.PENDING
    ).first()


def get_signature_summary(document):
    """
    Get a summary of all signatures for a document.
    
    Returns:
        dict with signature statistics
    
    Usage:
        summary = get_signature_summary(deployment)
        print(f"Signed: {summary['signed_count']}/{summary['total_count']}")
    """
    signatures = get_document_signatures(document)
    
    return {
        'total_count': signatures.count(),
        'signed_count': signatures.filter(status=SignatureStatus.SIGNED).count(),
        'pending_count': signatures.filter(status=SignatureStatus.PENDING).count(),
        'rejected_count': signatures.filter(status=SignatureStatus.REJECTED).count(),
        'expired_count': signatures.filter(status=SignatureStatus.EXPIRED).count(),
        'is_complete': all(sig.status == SignatureStatus.SIGNED for sig in signatures),
        'signatures': signatures
    }


def cancel_document_signatures(document, reason="Document cancelled"):
    """
    Cancel all pending signatures for a document.
    
    Usage:
        cancel_document_signatures(deployment, "Deployment was cancelled")
    """
    from apps.signatures.models import SignatureAuditLog
    
    signatures = get_document_signatures(document)
    pending_signatures = signatures.filter(status=SignatureStatus.PENDING)
    
    for sig in pending_signatures:
        sig.status = SignatureStatus.EXPIRED
        sig.comments = reason
        sig.save()
        
        # Log cancellation
        SignatureAuditLog.objects.create(
            signature=sig,
            action='cancelled',
            actor=None,
            details=reason
        )
    
    return pending_signatures.count()


# Template context helper
def add_signature_context(context, document, user):
    """
    Add signature-related variables to template context.
    
    Usage in view:
        context = {}
        add_signature_context(context, deployment, request.user)
        return render(request, 'template.html', context)
    """
    context['signatures'] = get_document_signatures(document)
    context['signature_summary'] = get_signature_summary(document)
    context['user_pending_signature'] = get_pending_signature_for_user(document, user)
    context['document_fully_signed'] = is_document_fully_signed(document)
    
    return context
