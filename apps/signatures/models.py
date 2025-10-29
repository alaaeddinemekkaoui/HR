from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.core.exceptions import ValidationError


class SignatureType(models.TextChoices):
    """Types of signatures in the HR system"""
    EMPLOYEE = 'employee', 'Employee Signature'
    MANAGER = 'manager', 'Manager/Supervisor Signature'
    HR_ADMIN = 'hr_admin', 'HR Administrator Signature'
    DIRECTOR = 'director', 'Director Signature'
    IT_ADMIN = 'it_admin', 'IT Administrator Signature'


class SignatureMethod(models.TextChoices):
    """Method used to capture signature"""
    DRAWN = 'drawn', 'Drawn on Canvas'
    TYPED = 'typed', 'Typed Name'
    USB_DEVICE = 'usb_device', 'USB Signature Device'
    BIOMETRIC = 'biometric', 'Biometric (Fingerprint)'
    USB_STAMP = 'usb_stamp', 'USB Digital Stamp (Password Protected)'


class SignatureStatus(models.TextChoices):
    """Status of a signature request"""
    PENDING = 'pending', 'Pending Signature'
    SIGNED = 'signed', 'Signed'
    REJECTED = 'rejected', 'Rejected'
    EXPIRED = 'expired', 'Expired'


class ElectronicSignature(models.Model):
    """
    Electronic signature record for any signable document in the system.
    Uses polymorphic relationship to support multiple document types.
    """
    # Who signed
    signer = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='signatures',
        help_text='User who provided the signature'
    )
    
    # Signature details
    signature_type = models.CharField(
        max_length=20,
        choices=SignatureType.choices,
        default=SignatureType.EMPLOYEE
    )
    signature_method = models.CharField(
        max_length=20,
        choices=SignatureMethod.choices,
        default=SignatureMethod.DRAWN,
        help_text='Method used to capture the signature'
    )
    status = models.CharField(
        max_length=20,
        choices=SignatureStatus.choices,
        default=SignatureStatus.PENDING
    )
    
    # Signature data
    signature_image = models.TextField(
        blank=True,
        help_text='Base64 encoded signature image drawn by user'
    )
    signature_text = models.CharField(
        max_length=255,
        blank=True,
        help_text='Typed signature (full name)'
    )
    
    # USB Device signature data
    usb_device_data = models.TextField(
        blank=True,
        help_text='Signature data from USB device (encrypted)'
    )
    usb_device_serial = models.CharField(
        max_length=100,
        blank=True,
        help_text='USB signature device serial number'
    )
    
    # USB Digital Stamp data (password-protected stamp image)
    usb_stamp_image = models.TextField(
        blank=True,
        help_text='Base64 encoded stamp image from USB (official company seal)'
    )
    usb_stamp_serial = models.CharField(
        max_length=100,
        blank=True,
        help_text='USB device serial containing the stamp'
    )
    usb_stamp_verified = models.BooleanField(
        default=False,
        help_text='Password verification successful for USB stamp'
    )
    # Optional reference to an uploaded, encrypted stamp artifact
    # If provided, this signature uses the artifact (any file type)
    # rather than a base64 inline image
    # This requires admin approval of the artifact
    stamp_artifact = models.ForeignKey(
        'signatures.StampArtifact',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='signatures',
        help_text='Approved encrypted stamp artifact used at signing time'
    )
    artifact_integrity_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text='SHA256 of plaintext artifact at time of signing for integrity verification'
    )
    
    # Biometric signature data
    biometric_data = models.TextField(
        blank=True,
        help_text='Fingerprint or biometric data (encrypted)'
    )
    biometric_type = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('fingerprint', 'Fingerprint'),
            ('face', 'Face Recognition'),
            ('iris', 'Iris Scan'),
        ],
        help_text='Type of biometric authentication used'
    )
    
    # Digital fingerprint for verification
    signature_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text='SHA256 hash for signature verification'
    )
    
    # IP and device tracking
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address when signature was made'
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text='Browser/device information'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text='When signature request was created')
    signed_at = models.DateTimeField(null=True, blank=True, help_text='When actually signed')
    expires_at = models.DateTimeField(null=True, blank=True, help_text='When signature request expires')
    
    # Comments
    comments = models.TextField(
        blank=True,
        help_text='Optional comments from signer (e.g., reason for rejection)'
    )
    
    # Generic relation to any document
    # Can be linked to: DeploymentForfaitaire, DeploymentReal, OrdreMission, Document, LeaveRequest, etc.
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text='Type of document being signed'
    )
    object_id = models.PositiveIntegerField(help_text='ID of the document')
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['signer', 'status']),
            models.Index(fields=['status', 'expires_at']),
        ]
        verbose_name = 'Electronic Signature'
        verbose_name_plural = 'Electronic Signatures'

    def __str__(self):
        return f"{self.signer.username} - {self.signature_type} - {self.status}"

    def clean(self):
        """Validate that at least one signature method is provided"""
        if self.status == SignatureStatus.SIGNED:
            if not self.signature_image and not self.signature_text:
                raise ValidationError('At least one signature method (image or text) must be provided')

    def save(self, *args, **kwargs):
        # Set signed_at when status changes to signed
        if self.status == SignatureStatus.SIGNED and not self.signed_at:
            self.signed_at = timezone.now()
        
        # Generate signature hash if not present
        if not self.signature_hash and self.status == SignatureStatus.SIGNED:
            self.signature_hash = self.generate_signature_hash()
        
        # Check expiration
        if self.expires_at and timezone.now() > self.expires_at and self.status == SignatureStatus.PENDING:
            self.status = SignatureStatus.EXPIRED
        
        super().save(*args, **kwargs)

    def generate_signature_hash(self):
        """Generate SHA256 hash of signature data for verification"""
        import hashlib
        core = self.signature_image or self.signature_text or ''
        # Include artifact integrity if present
        if self.stamp_artifact_id and self.artifact_integrity_hash:
            core = f"{core}:{self.stamp_artifact_id}:{self.artifact_integrity_hash}"
        data = f"{self.signer.id}:{self.signed_at}:{core}:{self.content_type_id}:{self.object_id}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_signature(self):
        """Verify signature hash integrity"""
        return self.signature_hash == self.generate_signature_hash()

    @property
    def is_expired(self):
        """Check if signature request has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at and self.status == SignatureStatus.PENDING
        return False

    @property
    def document_info(self):
        """Get information about the signed document"""
        if self.content_object:
            return {
                'type': self.content_type.model,
                'id': self.object_id,
                'object': self.content_object
            }
        return None


class SignatureWorkflow(models.Model):
    """
    Define signature workflow for different document types.
    Example: Deployment needs Employee → Manager → HR Admin → Director signatures
    """
    name = models.CharField(max_length=200, help_text='Workflow name')
    description = models.TextField(blank=True)
    
    # Document type this workflow applies to
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text='Type of document this workflow applies to'
    )
    
    # Workflow configuration
    required_signature_types = models.JSONField(
        default=list,
        help_text='Ordered list of required signature types ["employee", "manager", "hr_admin"]'
    )
    
    # Settings
    allow_parallel_signing = models.BooleanField(
        default=False,
        help_text='Allow multiple people to sign at the same time (vs sequential)'
    )
    signature_expiry_days = models.PositiveIntegerField(
        default=7,
        help_text='Days before signature request expires'
    )
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Signature Workflow'
        verbose_name_plural = 'Signature Workflows'

    def __str__(self):
        return f"{self.name} - {self.content_type.model}"


class SignatureAuditLog(models.Model):
    """
    Audit log for all signature-related actions.
    Immutable record for compliance and tracking.
    """
    signature = models.ForeignKey(
        ElectronicSignature,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    
    action = models.CharField(
        max_length=50,
        choices=[
            ('created', 'Signature Request Created'),
            ('viewed', 'Signature Page Viewed'),
            ('signed', 'Document Signed'),
            ('rejected', 'Signature Rejected'),
            ('expired', 'Signature Expired'),
            ('reminded', 'Reminder Sent'),
            ('cancelled', 'Signature Cancelled'),
        ]
    )
    
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text='User who performed the action'
    )
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    details = models.TextField(blank=True, help_text='Additional details about the action')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Signature Audit Log'
        verbose_name_plural = 'Signature Audit Logs'

    def __str__(self):
        return f"{self.action} - {self.signature} - {self.timestamp}"


class BiometricDevice(models.Model):
    """
    Register biometric devices (fingerprint readers, USB signature pads, etc.)
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='biometric_devices',
        help_text='User who owns this device'
    )
    
    device_type = models.CharField(
        max_length=50,
        choices=[
            ('fingerprint_reader', 'Fingerprint Reader'),
            ('usb_signature_pad', 'USB Signature Pad'),
            ('usb_stamp_device', 'USB Digital Stamp Device (Password Protected)'),
            ('face_camera', 'Face Recognition Camera'),
            ('iris_scanner', 'Iris Scanner'),
        ],
        help_text='Type of biometric device'
    )
    
    device_name = models.CharField(
        max_length=200,
        help_text='Device name/model'
    )
    
    device_serial = models.CharField(
        max_length=100,
        unique=True,
        help_text='Device serial number or unique ID'
    )
    
    device_fingerprint = models.CharField(
        max_length=256,
        help_text='Device hardware fingerprint for verification'
    )
    
    # Enrollment data
    enrollment_data = models.TextField(
        blank=True,
        help_text='Encrypted biometric enrollment template'
    )
    
    # USB Stamp specific data
    stamp_image_path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Encrypted path to stamp image on USB device'
    )
    stamp_password_hash = models.CharField(
        max_length=256,
        blank=True,
        help_text='Hashed password for USB stamp verification'
    )
    stamp_image_preview = models.TextField(
        blank=True,
        help_text='Base64 preview of stamp image (watermarked)'
    )
    
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(
        default=False,
        help_text='Device has been verified by admin'
    )
    
    registered_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    # Security
    failed_attempts = models.IntegerField(
        default=0,
        help_text='Number of failed authentication attempts'
    )
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Device locked until this time due to failed attempts'
    )
    
    class Meta:
        ordering = ['-registered_at']
        verbose_name = 'Biometric Device'
        verbose_name_plural = 'Biometric Devices'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_serial']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_device_type_display()}"
    
    def is_locked(self):
        """Check if device is currently locked"""
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False
    
    def record_failed_attempt(self):
        """Record failed authentication attempt"""
        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            # Lock for 30 minutes
            from datetime import timedelta
            self.locked_until = timezone.now() + timedelta(minutes=30)
        self.save()
    

class StampArtifact(models.Model):
    """
    Encrypted stamp artifact uploaded by a user (any file format).
    Stored encrypted at rest with integrity metadata and admin approval.
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stamp_artifacts',
        help_text='User who uploaded the stamp artifact'
    )
    related_device = models.ForeignKey(
        BiometricDevice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='stamp_artifacts',
        help_text='Optional device linked to this artifact'
    )
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, blank=True)
    file_size = models.BigIntegerField(default=0)
    # Encrypted blob fields
    ciphertext = models.BinaryField()
    nonce = models.BinaryField()  # AES-GCM nonce
    # Integrity of plaintext
    sha256_hash = models.CharField(max_length=64)
    # Admin approval
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_stamp_artifacts'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['owner', 'is_approved']),
        ]
        verbose_name = 'Stamp Artifact'
        verbose_name_plural = 'Stamp Artifacts'

    def __str__(self):
        status = 'approved' if self.is_approved else 'pending'
        return f"{self.original_filename} ({status})"

    def record_successful_use(self):
        """Record successful device use"""
        self.failed_attempts = 0
        self.locked_until = None
        self.last_used_at = timezone.now()
        self.save()

