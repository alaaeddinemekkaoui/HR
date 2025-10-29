from django.contrib import admin
from django.utils.html import format_html
from .models import ElectronicSignature, SignatureWorkflow, SignatureAuditLog, BiometricDevice


@admin.register(ElectronicSignature)
class ElectronicSignatureAdmin(admin.ModelAdmin):
    list_display = ['id', 'signer', 'signature_type', 'signature_method', 'status', 'content_type', 'signed_at', 'is_expired']
    list_filter = ['status', 'signature_type', 'signature_method', 'content_type', 'created_at']
    search_fields = ['signer__username', 'signer__first_name', 'signer__last_name']
    readonly_fields = ['signature_hash', 'created_at', 'signed_at', 'ip_address', 'user_agent']
    date_hierarchy = 'created_at'


@admin.register(SignatureWorkflow)
class SignatureWorkflowAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'is_active', 'allow_parallel_signing', 'signature_expiry_days']
    list_filter = ['is_active', 'content_type', 'allow_parallel_signing']
    search_fields = ['name', 'description']


@admin.register(SignatureAuditLog)
class SignatureAuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'signature', 'action', 'actor', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['signature__signer__username', 'actor__username']
    readonly_fields = ['signature', 'action', 'actor', 'ip_address', 'user_agent', 'timestamp']
    date_hierarchy = 'timestamp'


@admin.register(BiometricDevice)
class BiometricDeviceAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'device_type', 'device_name', 'is_verified', 'is_active', 'failed_attempts', 'registered_at', 'last_used_at']
    list_filter = ['device_type', 'is_verified', 'is_active', 'registered_at']
    search_fields = ['user__username', 'device_name', 'device_serial']
    readonly_fields = ['registered_at', 'last_used_at', 'device_serial', 'device_fingerprint', 'stamp_image_preview_display']
    date_hierarchy = 'registered_at'
    actions = ['verify_devices', 'deactivate_devices']
    
    fieldsets = (
        ('Device Information', {
            'fields': ('user', 'device_type', 'device_name', 'device_serial', 'device_fingerprint')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active', 'failed_attempts', 'locked_until')
        }),
        ('Biometric Data', {
            'fields': ('enrollment_data',),
            'classes': ('collapse',)
        }),
        ('USB Stamp Data', {
            'fields': ('stamp_image_path', 'stamp_password_hash', 'stamp_image_preview_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('registered_at', 'last_used_at')
        }),
    )
    
    def stamp_image_preview_display(self, obj):
        if obj.stamp_image_preview:
            return format_html('<img src="{}" style="max-width: 200px; max-height: 200px;"/>', obj.stamp_image_preview)
        return 'No preview available'
    stamp_image_preview_display.short_description = 'Stamp Preview'
    
    def verify_devices(self, request, queryset):
        count = queryset.update(is_verified=True)
        self.message_user(request, f'{count} device(s) verified successfully.')
    verify_devices.short_description = 'Verify selected devices'
    
    def deactivate_devices(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} device(s) deactivated.')
    deactivate_devices.short_description = 'Deactivate selected devices'
