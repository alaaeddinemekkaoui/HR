from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ElectronicSignature, SignatureStatus, SignatureAuditLog
from .utils import send_signature_notification


@receiver(post_save, sender=ElectronicSignature)
def signature_post_save(sender, instance, created, **kwargs):
    """
    Handle post-save actions for electronic signatures.
    """
    if created:
        # Send notification to signer
        send_signature_notification(instance)
        
        # Create audit log
        SignatureAuditLog.objects.create(
            signature=instance,
            action='created',
            actor=None,  # System action
            details=f'Signature request created for {instance.signer.get_full_name()}'
        )
    
    elif instance.status == SignatureStatus.SIGNED:
        # Signature was just completed
        # Could trigger additional workflows here
        pass
