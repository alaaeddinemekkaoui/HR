# Electronic Signature System - Implementation Guide

## Overview
The electronic signature system provides a complete solution for collecting digital signatures on HR documents (deployments, leave requests, etc.) with full audit trail, verification, and compliance features.

## Key Features

### 1. **Multi-Method Signature Capture**
   - **Draw Signature**: Canvas-based signature drawing (touch/mouse support)
   - **Type Signature**: Typed full name with stylized font
   - Base64 image encoding for storage

### 2. **Signature Types**
   - Employee Signature
   - Manager/Supervisor Signature
   - HR Administrator Signature
   - Director Signature
   - IT Administrator Signature

### 3. **Security & Compliance**
   - SHA256 hash generation for signature verification
   - IP address and user agent tracking
   - Immutable audit log for all actions
   - Signature expiration (configurable)
   - Signature integrity verification

### 4. **Workflow Support**
   - Sequential or parallel signature collection
   - Configurable signature workflows per document type
   - Automatic notification to signers
   - Rejection with reason tracking

### 5. **Audit Trail**
   - Every action logged (created, viewed, signed, rejected, expired)
   - Timestamp, actor, IP address, and details recorded
   - Compliance-ready for legal requirements

---

## Installation Steps

### 1. Run Migrations
```bash
docker compose exec web python manage.py makemigrations signatures
docker compose exec web python manage.py migrate signatures
```

### 2. Add Signature Permissions to Roles
Update `apps/roles/management/commands/seed_functions.py`:

```python
# Add signature permissions
signature_perms = [
    'signature.view',
    'signature.request',
    'signature.sign',
    'signature.reject',
    'signature.verify',
    'signature.admin',
]

# Assign to roles
it_admin_perms.extend(signature_perms)
hr_admin_perms.extend(['signature.view', 'signature.request', 'signature.verify', 'signature.admin'])
```

Run the seed command:
```bash
docker compose exec web python manage.py seed_functions
```

---

## Usage Examples

### Example 1: Request Signature for Deployment

```python
from apps.signatures.utils import create_signature_request
from apps.signatures.models import SignatureType
from apps.employees.models import Deployment

# Get deployment
deployment = Deployment.objects.get(id=1)

# Request employee signature
employee_signature = create_signature_request(
    document=deployment,
    signer=deployment.employee.user,
    signature_type=SignatureType.EMPLOYEE,
    expiry_days=7
)

# Request manager signature
manager_signature = create_signature_request(
    document=deployment,
    signer=deployment.employee.manager.user,
    signature_type=SignatureType.MANAGER,
    expiry_days=7
)

# Request HR admin signature
hr_admin = User.objects.filter(groups__name='HR Admin').first()
hr_signature = create_signature_request(
    document=deployment,
    signer=hr_admin,
    signature_type=SignatureType.HR_ADMIN,
    expiry_days=7
)
```

### Example 2: Create Signature Workflow

```python
from apps.signatures.models import SignatureWorkflow, SignatureType
from django.contrib.contenttypes.models import ContentType
from apps.employees.models import Deployment

# Create workflow for deployments
deployment_ct = ContentType.objects.get_for_model(Deployment)

workflow = SignatureWorkflow.objects.create(
    name='Deployment Approval Workflow',
    content_type=deployment_ct,
    required_signature_types=['employee', 'manager', 'hr_admin', 'director'],
    allow_parallel_signing=False,  # Sequential signing
    signature_expiry_days=7,
    is_active=True
)
```

### Example 3: Add Signature Request to Deployment Creation

Update your deployment view to automatically create signature requests:

```python
# In apps/employees/views/deployment_views.py

from apps.signatures.utils import create_signature_request
from apps.signatures.models import SignatureType

def create_deployment_view(request):
    if request.method == 'POST':
        form = DeploymentForm(request.POST)
        if form.is_valid():
            deployment = form.save()
            
            # Create signature requests
            # 1. Employee signature
            create_signature_request(
                document=deployment,
                signer=deployment.employee.user,
                signature_type=SignatureType.EMPLOYEE,
                expiry_days=7
            )
            
            # 2. Manager signature
            if deployment.employee.manager:
                create_signature_request(
                    document=deployment,
                    signer=deployment.employee.manager.user,
                    signature_type=SignatureType.MANAGER,
                    expiry_days=7
                )
            
            messages.success(request, 'Deployment created and signature requests sent!')
            return redirect('employees:deployment_detail', deployment.id)
    else:
        form = DeploymentForm()
    
    return render(request, 'employees/deployment_form.html', {'form': form})
```

### Example 4: Add Signature Button to Document Template

```html
<!-- In templates/employees/deployment_detail.html -->

{% load static %}

<!-- Signature Status Section -->
<div class="card mb-4">
    <div class="card-header bg-primary text-white">
        <h5 class="mb-0"><i class="bi bi-pen"></i> Signatures</h5>
    </div>
    <div class="card-body">
        <a href="{% url 'signatures:document_signatures' deployment.content_type.id deployment.id %}" 
           class="btn btn-info">
            <i class="bi bi-eye"></i> View All Signatures
        </a>
        
        <!-- Show pending signature requests for current user -->
        {% if user_pending_signature %}
        <a href="{% url 'signatures:sign_document' user_pending_signature.id %}" 
           class="btn btn-success">
            <i class="bi bi-pen"></i> Sign Now
        </a>
        {% endif %}
    </div>
</div>
```

### Example 5: Check if Document is Fully Signed

```python
from apps.signatures.models import ElectronicSignature, SignatureStatus
from django.contrib.contenttypes.models import ContentType

def is_document_fully_signed(document):
    """Check if all required signatures are collected"""
    content_type = ContentType.objects.get_for_model(document)
    
    signatures = ElectronicSignature.objects.filter(
        content_type=content_type,
        object_id=document.id
    )
    
    # Check if all signatures are signed
    return all(sig.status == SignatureStatus.SIGNED for sig in signatures)

# Usage
if is_document_fully_signed(deployment):
    deployment.status = 'approved'
    deployment.save()
```

### Example 6: Add Signature Link to Notification

```python
# In your notification creation code
from apps.notifications.models import Notification

def send_signature_notification(signature):
    """Send notification when signature is requested"""
    Notification.objects.create(
        user=signature.signer,
        title='Signature Required',
        message=f'Please review and sign the {signature.content_type.model}',
        notification_type='signature_request',
        link=f'/signatures/sign/{signature.id}/',
        is_read=False
    )
```

---

## Navigation Integration

### Add to Base Template Navigation

```html
<!-- In templates/base.html -->

<li class="nav-item">
    <a class="nav-link" href="{% url 'signatures:my_requests' %}">
        <i class="bi bi-pen"></i> My Signatures
        {% if pending_signature_count > 0 %}
        <span class="badge bg-danger">{{ pending_signature_count }}</span>
        {% endif %}
    </a>
</li>
```

### Add Context Processor for Pending Count

```python
# In apps/signatures/context_processors.py

from .models import ElectronicSignature, SignatureStatus

def pending_signatures(request):
    """Add pending signature count to all templates"""
    if request.user.is_authenticated:
        count = ElectronicSignature.objects.filter(
            signer=request.user,
            status=SignatureStatus.PENDING
        ).count()
        return {'pending_signature_count': count}
    return {'pending_signature_count': 0}
```

Add to settings.py:
```python
TEMPLATES = [
    {
        'OPTIONS': {
            'context_processors': [
                # ... existing processors
                'apps.signatures.context_processors.pending_signatures',
            ],
        },
    },
]
```

---

## API Endpoints

### Available URLs

```
/signatures/sign/<id>/                    - Sign a document
/signatures/reject/<id>/                  - Reject a signature request
/signatures/detail/<id>/                  - View signature details
/signatures/my-requests/                  - View my signature requests
/signatures/document/<ct_id>/<obj_id>/    - View all signatures for a document
/signatures/api/verify/<id>/              - Verify signature (JSON API)
```

---

## Security Best Practices

1. **Always verify signatures** before accepting as legally valid
2. **Store audit logs indefinitely** for compliance
3. **Use HTTPS** in production for secure transmission
4. **Set appropriate expiration** times (7-14 days typical)
5. **Backup signature data** regularly (includes base64 images)
6. **Test signature verification** regularly to ensure integrity

---

## Customization

### Custom Signature Fonts

Add to `static/css/iav-theme.css`:

```css
.signature-text {
    font-family: 'Brush Script MT', 'Lucida Handwriting', cursive;
    font-size: 36px;
    color: #000;
}
```

### Custom Signature Canvas Size

Modify in `templates/signatures/sign_document.html`:

```javascript
<canvas id="signatureCanvas" width="800" height="300"></canvas>
```

### Custom Expiration Logic

Override in your view:

```python
create_signature_request(
    document=deployment,
    signer=user,
    signature_type=SignatureType.EMPLOYEE,
    expiry_days=14  # 2 weeks instead of default 7 days
)
```

---

## Troubleshooting

### Signatures Not Appearing
- Check that migrations are applied: `python manage.py migrate signatures`
- Verify app is in INSTALLED_APPS
- Check URLs are included in main urls.py

### Canvas Not Working
- Ensure Bootstrap Icons are loaded
- Check browser console for JavaScript errors
- Test on different browsers (Chrome, Firefox, Safari)

### Signature Hash Mismatch
- This indicates signature tampering
- Check database integrity
- Verify no manual modifications to signature records

---

## Testing

```python
# Test signature creation
python manage.py shell

from apps.signatures.utils import create_signature_request
from apps.signatures.models import SignatureType
from apps.employees.models import Deployment
from django.contrib.auth.models import User

deployment = Deployment.objects.first()
user = User.objects.first()

sig = create_signature_request(
    document=deployment,
    signer=user,
    signature_type=SignatureType.EMPLOYEE
)

print(f"Signature created: {sig.id}")
print(f"Expires: {sig.expires_at}")
```

---

## Production Checklist

- [ ] Migrations applied to production database
- [ ] HTTPS enabled for secure transmission
- [ ] Signature permissions assigned to roles
- [ ] Email notifications configured for signature requests
- [ ] Audit log retention policy defined
- [ ] Backup strategy includes signature images
- [ ] Legal review of electronic signature policy
- [ ] User training on signature process
- [ ] Test signature verification process
- [ ] Monitor signature expiration and reminders

---

## Legal Compliance Notes

This electronic signature system is designed to comply with:
- **E-Sign Act (US)**: Electronic signatures have legal validity
- **UETA (Uniform Electronic Transactions Act)**
- **eIDAS (EU)**: Advanced electronic signatures

**Requirements met:**
✅ Signer identity verification (user authentication)
✅ Signature intent (explicit accept terms checkbox)
✅ Signature integrity (SHA256 hash verification)
✅ Audit trail (immutable logs with timestamps)
✅ Non-repudiation (IP address, user agent tracking)
✅ Document association (generic foreign key to any document)

**Note**: Consult with legal counsel to ensure compliance with your jurisdiction's specific requirements.
