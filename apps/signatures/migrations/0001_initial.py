# Generated migration file

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SignatureWorkflow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Workflow name', max_length=200)),
                ('description', models.TextField(blank=True)),
                ('required_signature_types', models.JSONField(default=list, help_text='Ordered list of required signature types ["employee", "manager", "hr_admin"]')),
                ('allow_parallel_signing', models.BooleanField(default=False, help_text='Allow multiple people to sign at the same time (vs sequential)')),
                ('signature_expiry_days', models.PositiveIntegerField(default=7, help_text='Days before signature request expires')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(help_text='Type of document this workflow applies to', on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Signature Workflow',
                'verbose_name_plural': 'Signature Workflows',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='ElectronicSignature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signature_type', models.CharField(choices=[('employee', 'Employee Signature'), ('manager', 'Manager/Supervisor Signature'), ('hr_admin', 'HR Administrator Signature'), ('director', 'Director Signature'), ('it_admin', 'IT Administrator Signature')], default='employee', max_length=20)),
                ('signature_method', models.CharField(choices=[('drawn', 'Drawn on Canvas'), ('typed', 'Typed Name'), ('usb_device', 'USB Signature Device'), ('biometric', 'Biometric (Fingerprint)')], default='drawn', help_text='Method used to capture the signature', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending Signature'), ('signed', 'Signed'), ('rejected', 'Rejected'), ('expired', 'Expired')], default='pending', max_length=20)),
                ('signature_image', models.TextField(blank=True, help_text='Base64 encoded signature image drawn by user')),
                ('signature_text', models.CharField(blank=True, help_text='Typed signature (full name)', max_length=255)),
                ('usb_device_data', models.TextField(blank=True, help_text='Signature data from USB device (encrypted)')),
                ('usb_device_serial', models.CharField(blank=True, help_text='USB signature device serial number', max_length=100)),
                ('biometric_data', models.TextField(blank=True, help_text='Fingerprint or biometric data (encrypted)')),
                ('biometric_type', models.CharField(blank=True, choices=[('fingerprint', 'Fingerprint'), ('face', 'Face Recognition'), ('iris', 'Iris Scan')], help_text='Type of biometric authentication used', max_length=50)),
                ('signature_hash', models.CharField(blank=True, help_text='SHA256 hash for signature verification', max_length=64)),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address when signature was made', null=True)),
                ('user_agent', models.CharField(blank=True, help_text='Browser/device information', max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When signature request was created')),
                ('signed_at', models.DateTimeField(blank=True, help_text='When actually signed', null=True)),
                ('expires_at', models.DateTimeField(blank=True, help_text='When signature request expires', null=True)),
                ('comments', models.TextField(blank=True, help_text='Optional comments from signer (e.g., reason for rejection)')),
                ('object_id', models.PositiveIntegerField(help_text='ID of the document')),
                ('content_type', models.ForeignKey(help_text='Type of document being signed', on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('signer', models.ForeignKey(help_text='User who provided the signature', on_delete=django.db.models.deletion.PROTECT, related_name='signatures', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Electronic Signature',
                'verbose_name_plural': 'Electronic Signatures',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='BiometricDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_type', models.CharField(choices=[('fingerprint_reader', 'Fingerprint Reader'), ('usb_signature_pad', 'USB Signature Pad'), ('face_camera', 'Face Recognition Camera'), ('iris_scanner', 'Iris Scanner')], help_text='Type of biometric device', max_length=50)),
                ('device_name', models.CharField(help_text='Device name/model', max_length=200)),
                ('device_serial', models.CharField(help_text='Device serial number or unique ID', max_length=100, unique=True)),
                ('device_fingerprint', models.CharField(help_text='Device hardware fingerprint for verification', max_length=256)),
                ('enrollment_data', models.TextField(blank=True, help_text='Encrypted biometric enrollment template')),
                ('is_active', models.BooleanField(default=True)),
                ('is_verified', models.BooleanField(default=False, help_text='Device has been verified by admin')),
                ('registered_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('failed_attempts', models.IntegerField(default=0, help_text='Number of failed authentication attempts')),
                ('locked_until', models.DateTimeField(blank=True, help_text='Device locked until this time due to failed attempts', null=True)),
                ('user', models.ForeignKey(help_text='User who owns this device', on_delete=django.db.models.deletion.CASCADE, related_name='biometric_devices', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Biometric Device',
                'verbose_name_plural': 'Biometric Devices',
                'ordering': ['-registered_at'],
            },
        ),
        migrations.CreateModel(
            name='SignatureAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('created', 'Signature Request Created'), ('viewed', 'Signature Page Viewed'), ('signed', 'Document Signed'), ('rejected', 'Signature Rejected'), ('expired', 'Signature Expired'), ('reminded', 'Reminder Sent'), ('cancelled', 'Signature Cancelled')], max_length=50)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.CharField(blank=True, max_length=500)),
                ('details', models.TextField(blank=True, help_text='Additional details about the action')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(help_text='User who performed the action', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('signature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='signatures.electronicsignature')),
            ],
            options={
                'verbose_name': 'Signature Audit Log',
                'verbose_name_plural': 'Signature Audit Logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='electronicsignature',
            index=models.Index(fields=['content_type', 'object_id'], name='signatures__content_f28d26_idx'),
        ),
        migrations.AddIndex(
            model_name='electronicsignature',
            index=models.Index(fields=['signer', 'status'], name='signatures__signer__03c1b7_idx'),
        ),
        migrations.AddIndex(
            model_name='electronicsignature',
            index=models.Index(fields=['status', 'expires_at'], name='signatures__status_43e3f7_idx'),
        ),
        migrations.AddIndex(
            model_name='biometricdevice',
            index=models.Index(fields=['user', 'is_active'], name='signatures__user_id_8d5c6a_idx'),
        ),
        migrations.AddIndex(
            model_name='biometricdevice',
            index=models.Index(fields=['device_serial'], name='signatures__device__7f0e9c_idx'),
        ),
    ]
