from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from .models import ElectronicSignature, SignatureStatus, SignatureAuditLog, BiometricDevice, StampArtifact
from .forms import SignatureForm, RejectSignatureForm, StampArtifactUploadForm
from .utils import get_client_ip, get_user_agent, encrypt_bytes, sha256_hex
from .decorators import it_admin_required


@login_required
def signature_request_view(request, signature_id):
    """
    View for displaying and processing a signature request.
    """
    signature = get_object_or_404(ElectronicSignature, id=signature_id)
    
    # Check if user is authorized to sign
    if signature.signer != request.user:
        messages.error(request, 'You are not authorized to sign this document.')
        return redirect('home')
    
    # Check if already signed
    if signature.status == SignatureStatus.SIGNED:
        messages.info(request, 'This document has already been signed.')
        return redirect('signature_detail', signature_id=signature_id)
    
    # Check if expired
    if signature.is_expired:
        signature.status = SignatureStatus.EXPIRED
        signature.save()
        messages.error(request, 'This signature request has expired.')
        return redirect('signature_detail', signature_id=signature_id)
    
    # Log view
    SignatureAuditLog.objects.create(
        signature=signature,
        action='viewed',
        actor=request.user,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    if request.method == 'POST':
        form = SignatureForm(request.POST, instance=signature)
        if form.is_valid():
            signature = form.save(commit=False)
            signature.status = SignatureStatus.SIGNED
            signature.signed_at = timezone.now()
            signature.ip_address = get_client_ip(request)
            signature.user_agent = get_user_agent(request)
            signature.save()
            
            # Log signature
            SignatureAuditLog.objects.create(
                signature=signature,
                action='signed',
                actor=request.user,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details=f"Document signed successfully"
            )
            
            messages.success(request, 'Document signed successfully!')
            
            # Check if all signatures are complete for the document
            check_document_completion(signature)
            
            return redirect('signature_detail', signature_id=signature_id)
    else:
        form = SignatureForm(instance=signature)
    
    # User's approved stamp artifacts (for USB stamp method)
    approved_artifacts = StampArtifact.objects.filter(owner=request.user, is_approved=True).only('id', 'original_filename')

    context = {
        'signature': signature,
        'form': form,
        'document': signature.content_object,
        'document_type': signature.content_type.model,
        'approved_artifacts': approved_artifacts,
    }
    return render(request, 'signatures/sign_document.html', context)


@login_required
def reject_signature_view(request, signature_id):
    """
    View for rejecting a signature request.
    """
    signature = get_object_or_404(ElectronicSignature, id=signature_id)
    
    # Check if user is authorized
    if signature.signer != request.user:
        messages.error(request, 'You are not authorized to reject this signature request.')
        return redirect('home')
    
    if request.method == 'POST':
        form = RejectSignatureForm(request.POST)
        if form.is_valid():
            signature.status = SignatureStatus.REJECTED
            signature.comments = form.cleaned_data['reason']
            signature.save()
            
            # Log rejection
            SignatureAuditLog.objects.create(
                signature=signature,
                action='rejected',
                actor=request.user,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details=f"Reason: {signature.comments}"
            )
            
            messages.warning(request, 'Signature request has been rejected.')
            return redirect('signature_detail', signature_id=signature_id)
    else:
        form = RejectSignatureForm()
    
    context = {
        'signature': signature,
        'form': form,
        'document': signature.content_object,
    }
    return render(request, 'signatures/reject_signature.html', context)


@login_required
def signature_detail_view(request, signature_id):
    """
    View for displaying signature details and verification.
    """
    signature = get_object_or_404(ElectronicSignature, id=signature_id)
    
    # Check authorization - signer or staff can view
    if signature.signer != request.user and not request.user.is_staff:
        messages.error(request, 'You are not authorized to view this signature.')
        return redirect('home')
    
    # Verify signature integrity
    is_valid = signature.verify_signature() if signature.status == SignatureStatus.SIGNED else None
    
    # Get audit logs
    audit_logs = signature.audit_logs.all()[:20]
    
    context = {
        'signature': signature,
        'document': signature.content_object,
        'document_type': signature.content_type.model,
        'is_valid': is_valid,
        'audit_logs': audit_logs,
    }
    return render(request, 'signatures/signature_detail.html', context)


@login_required
def my_signature_requests_view(request):
    """
    View for displaying all signature requests for the current user.
    """
    pending_signatures = ElectronicSignature.objects.filter(
        signer=request.user,
        status=SignatureStatus.PENDING
    ).select_related('content_type')
    
    completed_signatures = ElectronicSignature.objects.filter(
        signer=request.user,
        status__in=[SignatureStatus.SIGNED, SignatureStatus.REJECTED]
    ).select_related('content_type')[:20]
    
    context = {
        'pending_signatures': pending_signatures,
        'completed_signatures': completed_signatures,
    }
    return render(request, 'signatures/my_requests.html', context)


@login_required
def upload_stamp_artifact_view(request):
    """
    Upload a stamp artifact (any file format). The file is encrypted at rest and
    awaits IT Admin approval before it can be used for signing.
    """
    if request.method == 'POST':
        form = StampArtifactUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = form.cleaned_data['file']
            device_id = form.cleaned_data.get('device_id')
            raw = f.read()
            integrity = sha256_hex(raw)
            try:
                ciphertext, nonce = encrypt_bytes(raw)
            except Exception as e:
                messages.error(request, f'Encryption failed: {e}')
                return redirect('signatures:upload_artifact')

            related_device = None
            if device_id:
                try:
                    related_device = BiometricDevice.objects.get(id=device_id, user=request.user)
                except BiometricDevice.DoesNotExist:
                    related_device = None

            StampArtifact.objects.create(
                owner=request.user,
                related_device=related_device,
                original_filename=getattr(f, 'name', 'artifact'),
                mime_type=getattr(f, 'content_type', '') or '',
                file_size=getattr(f, 'size', 0) or 0,
                ciphertext=ciphertext,
                nonce=nonce,
                sha256_hash=integrity,
                is_approved=False
            )

            messages.success(request, 'Stamp uploaded securely. Awaiting IT Admin approval.')
            return redirect('signatures:my_requests')
    else:
        form = StampArtifactUploadForm()

    return render(request, 'signatures/upload_stamp_artifact.html', {'form': form})


@login_required
def document_signatures_view(request, content_type_id, object_id):
    """
    View for displaying all signatures for a specific document.
    """
    content_type = get_object_or_404(ContentType, id=content_type_id)
    model_class = content_type.model_class()
    document = get_object_or_404(model_class, id=object_id)
    
    # Check if user has permission to view (staff or document owner)
    if not request.user.is_staff and not hasattr(document, 'employee'):
        messages.error(request, 'You do not have permission to view this.')
        return redirect('home')
    
    signatures = ElectronicSignature.objects.filter(
        content_type=content_type,
        object_id=object_id
    ).select_related('signer').order_by('created_at')
    
    context = {
        'document': document,
        'document_type': content_type.model,
        'signatures': signatures,
        'all_signed': all(s.status == SignatureStatus.SIGNED for s in signatures),
    }
    return render(request, 'signatures/document_signatures.html', context)


@require_http_methods(["POST"])
@login_required
def verify_signature_api(request, signature_id):
    """
    API endpoint to verify signature integrity.
    """
    signature = get_object_or_404(ElectronicSignature, id=signature_id)
    
    is_valid = signature.verify_signature()
    
    return JsonResponse({
        'valid': is_valid,
        'signature_id': signature.id,
        'status': signature.status,
        'signed_at': signature.signed_at.isoformat() if signature.signed_at else None,
        'signer': signature.signer.get_full_name() or signature.signer.username,
    })


def check_document_completion(signature):
    """
    Check if all required signatures for a document are complete.
    Update document status if all signatures are collected.
    """
    all_signatures = ElectronicSignature.objects.filter(
        content_type=signature.content_type,
        object_id=signature.object_id
    )
    
    if all(s.status == SignatureStatus.SIGNED for s in all_signatures):
        # All signatures complete - update document
        document = signature.content_object
        if hasattr(document, 'signature_complete'):
            document.signature_complete = True
            document.save()
        
        # Log completion
        SignatureAuditLog.objects.create(
            signature=signature,
            action='completed',
            actor=signature.signer,
            details='All signatures collected - document complete'
        )


@login_required
@it_admin_required
def admin_signatures_dashboard(request):
    """
    Admin dashboard for IT Admins to manage signature system.
    Only IT Admins can access this view.
    """
    from django.db.models import Count, Q
    
    # Pending devices awaiting verification
    pending_devices = BiometricDevice.objects.filter(
        is_verified=False,
        is_active=True
    ).select_related('user').order_by('-registered_at')
    
    # Recent signatures
    recent_signatures = ElectronicSignature.objects.select_related(
        'signer', 'content_type'
    ).order_by('-created_at')[:20]
    
    # Statistics
    stats = {
        'total_signatures': ElectronicSignature.objects.count(),
        'pending_signatures': ElectronicSignature.objects.filter(status=SignatureStatus.PENDING).count(),
        'signed_today': ElectronicSignature.objects.filter(
            signed_at__date=timezone.now().date()
        ).count(),
        'total_devices': BiometricDevice.objects.count(),
        'pending_devices': pending_devices.count(),
        'active_devices': BiometricDevice.objects.filter(is_active=True, is_verified=True).count(),
    }
    
    # Signature by method
    signature_methods = ElectronicSignature.objects.filter(
        status=SignatureStatus.SIGNED
    ).values('signature_method').annotate(count=Count('id'))
    
    # Pending artifacts
    pending_artifacts = StampArtifact.objects.filter(is_approved=False).select_related('owner')[:20]

    context = {
        'stats': stats,
        'pending_devices': pending_devices,
        'recent_signatures': recent_signatures,
        'signature_methods': signature_methods,
        'pending_artifacts': pending_artifacts,
    }
    
    return render(request, 'signatures/admin_dashboard.html', context)


@login_required
@it_admin_required
def admin_verify_device(request, device_id):
    """
    IT Admin: Verify a biometric device
    """
    device = get_object_or_404(BiometricDevice, id=device_id)
    
    device.is_verified = True
    device.save()
    
    messages.success(request, f'Device "{device.device_name}" for user {device.user.username} has been verified.')
    return redirect('signatures:admin_dashboard')


@login_required
@it_admin_required  
def admin_deactivate_device(request, device_id):
    """
    IT Admin: Deactivate a biometric device
    """
    device = get_object_or_404(BiometricDevice, id=device_id)
    
    device.is_active = False
    device.save()
    
    messages.warning(request, f'Device "{device.device_name}" for user {device.user.username} has been deactivated.')
    return redirect('signatures:admin_dashboard')


@login_required
@it_admin_required
def admin_stamp_artifacts_view(request):
    """List and approve pending encrypted stamp artifacts."""
    pending = StampArtifact.objects.filter(is_approved=False).select_related('owner').order_by('-uploaded_at')
    approved = StampArtifact.objects.filter(is_approved=True).select_related('owner').order_by('-approved_at')[:20]
    return render(request, 'signatures/admin_artifacts.html', {
        'pending': pending,
        'approved': approved,
    })


@login_required
@it_admin_required
def admin_approve_artifact_view(request, artifact_id):
    art = get_object_or_404(StampArtifact, id=artifact_id)
    if art.is_approved:
        messages.info(request, 'Artifact already approved.')
        return redirect('signatures:admin_artifacts')
    art.is_approved = True
    art.approved_by = request.user
    art.approved_at = timezone.now()
    art.save()
    messages.success(request, f'Artifact "{art.original_filename}" approved.')
    return redirect('signatures:admin_artifacts')
