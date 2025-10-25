from django.db import models
from django.contrib.auth.models import Group


class RoleDefinition(models.Model):
    """
    Defines a custom role with descriptive information.
    Maps 1:1 to Django Group for permission assignment.
    """
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='role_definition')
    description = models.TextField(blank=True, help_text='What this role is for')
    is_system_role = models.BooleanField(default=False, help_text='System roles cannot be deleted')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Role Definition'
        verbose_name_plural = 'Role Definitions'
        ordering = ['group__name']

    def __str__(self):
        return self.group.name


class FunctionPermission(models.Model):
    """
    Defines available functions/actions in the system that can be assigned to roles.
    Examples: 'employees.view', 'employees.add', 'employees.edit', 'employees.delete',
              'users.manage', 'roles.manage', 'dashboard.access'
    """
    code = models.CharField(max_length=100, unique=True, help_text='Unique code like employees.view')
    name = models.CharField(max_length=200, help_text='Human-readable name')
    description = models.TextField(blank=True)
    module = models.CharField(max_length=100, help_text='Module/app this belongs to (e.g., employees, users)')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Function Permission'
        verbose_name_plural = 'Function Permissions'
        ordering = ['module', 'code']

    def __str__(self):
        return f"{self.module}: {self.name}"


class RolePermissionMapping(models.Model):
    """
    Maps roles to function permissions.
    Allows fine-grained control: each role can have specific functions enabled.
    """
    role = models.ForeignKey(RoleDefinition, on_delete=models.CASCADE, related_name='permission_mappings')
    function = models.ForeignKey(FunctionPermission, on_delete=models.CASCADE, related_name='role_mappings')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Role Permission Mapping'
        verbose_name_plural = 'Role Permission Mappings'
        unique_together = ('role', 'function')
        ordering = ['role', 'function__module', 'function__code']

    def __str__(self):
        return f"{self.role.group.name} -> {self.function.code}"
