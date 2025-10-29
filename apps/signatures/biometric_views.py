from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import BiometricDevice, ElectronicSignature, SignatureMethod, StampArtifact
import json
import hashlib


@login_required
def register_biometric_device_view(request):
    """
    View for registering a new biometric device (USB signature pad, fingerprint reader, USB stamp, etc.)
    """
    if request.method == 'POST':
        device_type = request.POST.get('device_type')
        device_name = request.POST.get('device_name')
        device_serial = request.POST.get('device_serial')
        device_fingerprint = request.POST.get('device_fingerprint')
        enrollment_data = request.POST.get('enrollment_data', '')
        
        # USB Stamp specific fields
        stamp_password = request.POST.get('stamp_password', '')
        stamp_image = request.POST.get('stamp_image', '')
        stamp_image_preview = request.POST.get('stamp_image_preview', '')
        
        # Check if device already registered
        if BiometricDevice.objects.filter(device_serial=device_serial).exists():
            messages.error(request, 'This device is already registered.')
            return redirect('signatures:register_device')
        
        # Hash password for USB stamp devices
        stamp_password_hash = ''
        if device_type == 'usb_stamp_device' and stamp_password:
            stamp_password_hash = hashlib.sha256(stamp_password.encode()).hexdigest()
        
        # Create device registration
        device = BiometricDevice.objects.create(
            user=request.user,
            device_type=device_type,
            device_name=device_name,
            device_serial=device_serial,
            device_fingerprint=device_fingerprint,
            enrollment_data=enrollment_data,
            stamp_password_hash=stamp_password_hash,
            stamp_image_path=stamp_image if device_type == 'usb_stamp_device' else '',
            stamp_image_preview=stamp_image_preview if device_type == 'usb_stamp_device' else '',
            is_active=True,
            is_verified=False  # Requires admin verification
        )
        
        device_type_name = dict(BiometricDevice._meta.get_field('device_type').choices).get(device_type, device_type)
        messages.success(request, f'{device_type_name} registered! Awaiting admin verification.')
        return redirect('signatures:my_devices')
    
    # Allow preselecting a device type via GET parameter (e.g., ?device_type=fingerprint_reader)
    preselect = request.GET.get('device_type', '')
    return render(request, 'signatures/register_device.html', {'preselect_device_type': preselect})


@login_required
def my_biometric_devices_view(request):
    """
    View for managing user's biometric devices
    """
    devices = BiometricDevice.objects.filter(user=request.user)
    
    context = {
        'devices': devices,
    }
    return render(request, 'signatures/my_devices.html', context)


@login_required
def deactivate_device_view(request, device_id):
    """
    Deactivate a biometric device
    """
    device = get_object_or_404(BiometricDevice, id=device_id, user=request.user)
    
    device.is_active = False
    device.save()
    messages.success(request, f'Device "{device.device_name}" has been deactivated.')
    return redirect('signatures:my_devices')


@require_http_methods(["POST"])
@login_required
def detect_usb_signature_device_api(request):
    """
    API endpoint to detect USB signature device
    Called from JavaScript when USB device is connected
    """
    try:
        data = json.loads(request.body)
        device_serial = data.get('device_serial')
        device_name = data.get('device_name')
        
        # Check if device is registered for this user
        device = BiometricDevice.objects.filter(
            user=request.user,
            device_serial=device_serial,
            device_type='usb_signature_pad',
            is_active=True,
            is_verified=True
        ).first()
        
        if device:
            if device.is_locked():
                return JsonResponse({
                    'detected': False,
                    'error': 'Device is locked due to multiple failed attempts'
                }, status=403)
            
            return JsonResponse({
                'detected': True,
                'device_id': device.id,
                'device_name': device.device_name,
                'last_used': device.last_used_at.isoformat() if device.last_used_at else None
            })
        else:
            return JsonResponse({
                'detected': False,
                'registered': False,
                'message': 'Device not registered or not verified'
            })
    
    except Exception as e:
        return JsonResponse({
            'detected': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def verify_fingerprint_api(request):
    """
    API endpoint to verify fingerprint for signature
    """
    try:
        data = json.loads(request.body)
        device_serial = data.get('device_serial')
        fingerprint_data = data.get('fingerprint_data')
        
        # Check if fingerprint reader is registered
        device = BiometricDevice.objects.filter(
            user=request.user,
            device_serial=device_serial,
            device_type='fingerprint_reader',
            is_active=True,
            is_verified=True
        ).first()
        
        if not device:
            return JsonResponse({
                'verified': False,
                'error': 'Fingerprint reader not registered or not verified'
            }, status=404)
        
        if device.is_locked():
            return JsonResponse({
                'verified': False,
                'error': 'Device is locked due to multiple failed attempts'
            }, status=403)
        
        # Verify fingerprint against enrolled template
        # In production, use proper biometric matching algorithm
        # For now, simple comparison (THIS IS NOT SECURE - use proper biometric SDK)
        if fingerprint_data == device.enrollment_data:
            device.record_successful_use()
            
            return JsonResponse({
                'verified': True,
                'device_id': device.id,
                'message': 'Fingerprint verified successfully'
            })
        else:
            device.record_failed_attempt()
            
            return JsonResponse({
                'verified': False,
                'attempts_remaining': max(0, 5 - device.failed_attempts),
                'error': 'Fingerprint does not match'
            }, status=401)
    
    except Exception as e:
        return JsonResponse({
            'verified': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def sign_with_usb_device_api(request):
    """
    API endpoint to sign document with USB signature device
    """
    try:
        data = json.loads(request.body)
        signature_id = data.get('signature_id')
        device_serial = data.get('device_serial')
        signature_data = data.get('signature_data')
        
        signature = get_object_or_404(ElectronicSignature, id=signature_id, signer=request.user)
        
        # Verify device
        device = BiometricDevice.objects.filter(
            user=request.user,
            device_serial=device_serial,
            device_type='usb_signature_pad',
            is_active=True,
            is_verified=True
        ).first()
        
        if not device:
            return JsonResponse({
                'success': False,
                'error': 'USB signature device not registered or verified'
            }, status=404)
        
        if device.is_locked():
            return JsonResponse({
                'success': False,
                'error': 'Device is locked'
            }, status=403)
        
        # Save signature
        signature.signature_method = SignatureMethod.USB_DEVICE
        signature.usb_device_data = signature_data
        signature.usb_device_serial = device_serial
        signature.status = 'signed'
        signature.signed_at = timezone.now()
        signature.save()
        
        device.record_successful_use()
        
        return JsonResponse({
            'success': True,
            'message': 'Document signed successfully with USB device',
            'signature_id': signature.id
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def sign_with_usb_stamp_api(request):
    """
    API endpoint to sign document with USB digital stamp (password protected)
    """
    try:
        data = json.loads(request.body)
        signature_id = data.get('signature_id')
        device_serial = data.get('device_serial')
        stamp_password = data.get('stamp_password')
        stamp_image = data.get('stamp_image')
        artifact_id = data.get('artifact_id')
        
        signature = get_object_or_404(ElectronicSignature, id=signature_id, signer=request.user)
        
        # Verify device
        device = BiometricDevice.objects.filter(
            user=request.user,
            device_serial=device_serial,
            device_type='usb_stamp_device',
            is_active=True,
            is_verified=True
        ).first()
        
        if not device:
            return JsonResponse({
                'success': False,
                'error': 'USB stamp device not registered or verified'
            }, status=404)
        
        if device.is_locked():
            return JsonResponse({
                'success': False,
                'error': 'Device is locked due to too many failed attempts'
            }, status=403)
        
        # Verify password
        password_hash = hashlib.sha256(stamp_password.encode()).hexdigest()
        if password_hash != device.stamp_password_hash:
            device.record_failed_attempt()
            attempts_left = 5 - device.failed_attempts
            return JsonResponse({
                'success': False,
                'error': f'Invalid password. {attempts_left} attempts remaining.'
            }, status=401)
        
        # Save signature with stamp (artifact preferred if provided and approved)
        signature.signature_method = SignatureMethod.USB_STAMP
        signature.usb_stamp_serial = device_serial
        signature.usb_stamp_verified = True

        if artifact_id:
            art = StampArtifact.objects.filter(id=artifact_id, owner=request.user, is_approved=True).first()
            if not art:
                return JsonResponse({
                    'success': False,
                    'error': 'Stamp artifact not found or not approved'
                }, status=400)
            signature.stamp_artifact = art
            signature.artifact_integrity_hash = art.sha256_hash
            signature.usb_stamp_image = ''
        else:
            signature.usb_stamp_image = stamp_image or ''

        signature.status = 'signed'
        signature.signed_at = timezone.now()
        signature.ip_address = request.META.get('REMOTE_ADDR')
        signature.user_agent = request.META.get('HTTP_USER_AGENT', '')
        signature.save()
        
        device.record_successful_use()
        
        return JsonResponse({
            'success': True,
            'message': 'Document signed successfully with digital stamp',
            'signature_id': signature.id
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def verify_usb_stamp_password_api(request):
    """
    API endpoint to verify USB stamp password before loading stamp image
    """
    try:
        data = json.loads(request.body)
        device_serial = data.get('device_serial')
        password = data.get('password')
        
        # Verify device
        device = BiometricDevice.objects.filter(
            user=request.user,
            device_serial=device_serial,
            device_type='usb_stamp_device',
            is_active=True,
            is_verified=True
        ).first()
        
        if not device:
            return JsonResponse({
                'success': False,
                'error': 'USB stamp device not found'
            }, status=404)
        
        if device.is_locked():
            lock_minutes = int((device.locked_until - timezone.now()).total_seconds() / 60)
            return JsonResponse({
                'success': False,
                'error': f'Device is locked for {lock_minutes} more minutes'
            }, status=403)
        
        # Verify password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash != device.stamp_password_hash:
            device.record_failed_attempt()
            attempts_left = 5 - device.failed_attempts
            return JsonResponse({
                'success': False,
                'error': f'Invalid password',
                'attempts_remaining': attempts_left
            }, status=401)
        
        # Password correct - reset failed attempts and return stamp image
        device.failed_attempts = 0
        device.save()
        
        return JsonResponse({
            'success': True,
            'stamp_image': device.stamp_image_path,
            'stamp_preview': device.stamp_image_preview,
            'device_name': device.device_name
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
@login_required
def sign_with_biometric_api(request):
    """
    API endpoint to sign document with biometric (fingerprint)
    """
    try:
        data = json.loads(request.body)
        signature_id = data.get('signature_id')
        device_serial = data.get('device_serial')
        biometric_data = data.get('biometric_data')
        biometric_type = data.get('biometric_type', 'fingerprint')
        
        signature = get_object_or_404(ElectronicSignature, id=signature_id, signer=request.user)
        
        # Verify device
        device = BiometricDevice.objects.filter(
            user=request.user,
            device_serial=device_serial,
            device_type='fingerprint_reader',
            is_active=True,
            is_verified=True
        ).first()
        
        if not device:
            return JsonResponse({
                'success': False,
                'error': 'Biometric device not registered or verified'
            }, status=404)
        
        if device.is_locked():
            return JsonResponse({
                'success': False,
                'error': 'Device is locked'
            }, status=403)
        
        # Verify biometric
        # In production, use proper biometric verification
        if biometric_data != device.enrollment_data:
            device.record_failed_attempt()
            return JsonResponse({
                'success': False,
                'error': 'Biometric verification failed'
            }, status=401)
        
        # Save signature
        signature.signature_method = SignatureMethod.BIOMETRIC
        signature.biometric_data = biometric_data
        signature.biometric_type = biometric_type
        signature.status = 'signed'
        signature.signed_at = timezone.now()
        signature.save()
        
        device.record_successful_use()
        
        return JsonResponse({
            'success': True,
            'message': 'Document signed successfully with biometric',
            'signature_id': signature.id
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
