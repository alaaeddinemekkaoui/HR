from django.contrib import admin
from .models import RoleDefinition, FunctionPermission, RolePermissionMapping


@admin.register(RoleDefinition)
class RoleDefinitionAdmin(admin.ModelAdmin):
    list_display = ('group', 'description', 'is_system_role', 'created_at')
    list_filter = ('is_system_role',)
    search_fields = ('group__name', 'description')


@admin.register(FunctionPermission)
class FunctionPermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'module', 'is_active')
    list_filter = ('module', 'is_active')
    search_fields = ('code', 'name', 'module')


@admin.register(RolePermissionMapping)
class RolePermissionMappingAdmin(admin.ModelAdmin):
    list_display = ('role', 'function', 'granted_at')
    list_filter = ('role', 'function__module')
    search_fields = ('role__group__name', 'function__code')
