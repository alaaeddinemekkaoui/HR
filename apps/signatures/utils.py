def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Get user agent from request."""
    return request.META.get('HTTP_USER_AGENT', '')[:500]


# --- Encryption utilities for stamp artifacts ---
import os
import hashlib
from typing import Tuple
from django.conf import settings

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except Exception:
    AESGCM = None  # Will surface at runtime if not installed


def _get_master_key() -> bytes:
    """Derive a 32-byte key from Django SECRET_KEY for AES-GCM.
    Note: For production, consider a separate, rotated key and a KDF with salt.
    """
    sk = settings.SECRET_KEY.encode('utf-8')
    return hashlib.sha256(sk).digest()


def encrypt_bytes(plaintext: bytes, aad: bytes = b"") -> Tuple[bytes, bytes]:
    """Encrypt bytes using AES-GCM with app master key.
    Returns (ciphertext, nonce).
    """
    if AESGCM is None:
        raise RuntimeError("cryptography is not installed; cannot encrypt")
    key = _get_master_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
    return ciphertext, nonce


def decrypt_bytes(ciphertext: bytes, nonce: bytes, aad: bytes = b"") -> bytes:
    """Decrypt bytes using AES-GCM with app master key."""
    if AESGCM is None:
        raise RuntimeError("cryptography is not installed; cannot decrypt")
    key = _get_master_key()
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, aad)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def create_signature_request(document, signer, signature_type, expiry_days=7):
    """
    Helper function to create a signature request for a document.
    
    Args:
        document: The document object to be signed
        signer: User who should sign
        signature_type: Type of signature (from SignatureType)
        expiry_days: Days until signature request expires (default 7)
    
    Returns:
        ElectronicSignature object
    """
    from django.contrib.contenttypes.models import ContentType
    from django.utils import timezone
    from datetime import timedelta
    from .models import ElectronicSignature, SignatureStatus
    
    content_type = ContentType.objects.get_for_model(document)
    
    signature = ElectronicSignature.objects.create(
        signer=signer,
        signature_type=signature_type,
        status=SignatureStatus.PENDING,
        content_type=content_type,
        object_id=document.id,
        expires_at=timezone.now() + timedelta(days=expiry_days)
    )
    
    return signature


def create_workflow_signatures(document, workflow):
    """
    Create all signature requests based on a workflow.
    
    Args:
        document: The document object to be signed
        workflow: SignatureWorkflow object
    
    Returns:
        List of ElectronicSignature objects
    """
    from .models import ElectronicSignature
    
    signatures = []
    
    # Get required signers based on workflow
    # This would need to be customized based on your document model
    # Example: for deployment, might need employee, manager, hr_admin, director
    
    for signature_type in workflow.required_signature_types:
        # Determine who should sign based on signature_type
        signer = get_signer_for_type(document, signature_type)
        
        if signer:
            signature = create_signature_request(
                document=document,
                signer=signer,
                signature_type=signature_type,
                expiry_days=workflow.signature_expiry_days
            )
            signatures.append(signature)
    
    return signatures


def get_signer_for_type(document, signature_type):
    """
    Determine who should sign based on signature type and document.
    
    This needs to be customized based on your models.
    """
    from .models import SignatureType
    
    # Example logic - customize based on your needs
    if signature_type == SignatureType.EMPLOYEE:
        return document.employee.user if hasattr(document, 'employee') else None
    
    elif signature_type == SignatureType.MANAGER:
        # Get employee's manager
        if hasattr(document, 'employee') and hasattr(document.employee, 'manager'):
            return document.employee.manager.user
        return None
    
    elif signature_type == SignatureType.HR_ADMIN:
        # Get HR admin from roles
        from apps.roles.models import RolePermission
        hr_role = RolePermission.objects.filter(
            permission__name='hr_admin'
        ).first()
        if hr_role:
            return hr_role.role.users.first()
        return None
    
    elif signature_type == SignatureType.DIRECTOR:
        # Get director - might be from organization structure
        from apps.employees.models import Service
        if hasattr(document, 'employee'):
            service = document.employee.service
            # Assuming director is stored somewhere in org structure
            return None  # Implement based on your structure
        return None
    
    return None


def send_signature_notification(signature):
    """
    Send notification to signer about pending signature request.
    
    This integrates with your existing notifications system.
    """
    from apps.notifications.models import Notification
    
    Notification.objects.create(
        user=signature.signer,
        title='Signature Required',
        message=f'You have a document waiting for your signature: {signature.content_type.model}',
        notification_type='signature_request',
        link=f'/signatures/sign/{signature.id}/'
    )
