from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from .forms import GroupPermissionForm, UserRoleForm
from .models import RoleDefinition, FunctionPermission, RolePermissionMapping


class ITAdminOnlyMixin(UserPassesTestMixin):
    def test_user_passes(self, user):
        return user.is_authenticated and user.groups.filter(name='IT Admin').exists()

    def test_func(self):
        return self.test_user_passes(self.request.user)


class RolesInfoView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        return render(request, 'roles/index.html', {})


class GroupListView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        # Ensure IT Admin group remains unmodifiable with full permissions
        self._ensure_it_admin_full_permissions()
        groups = Group.objects.all().order_by('name')
        employee_ct = ContentType.objects.get(app_label='employees', model='employee')
        perms_map = {}
        for g in groups:
            perms = g.permissions.filter(content_type=employee_ct).values_list('codename', flat=True)
            perms_map[g.id] = set(perms)
        return render(request, 'roles/groups.html', {
            'groups': groups,
            'perms_map': perms_map,
        })

    def _ensure_it_admin_full_permissions(self):
        it_admin, _ = Group.objects.get_or_create(name='IT Admin')
        # Assign ALL Django model permissions
        all_perms = Permission.objects.all()
        it_admin.permissions.set(all_perms)
        # Ensure role definition exists and is marked as system role
        role_def, _ = RoleDefinition.objects.get_or_create(group=it_admin, defaults={'description': 'System IT Admin', 'is_system_role': True})
        if not role_def.is_system_role:
            role_def.is_system_role = True
            role_def.save()
        # Assign all function permissions
        functions = FunctionPermission.objects.filter(is_active=True)
        RolePermissionMapping.objects.filter(role=role_def).delete()
        RolePermissionMapping.objects.bulk_create([
            RolePermissionMapping(role=role_def, function=f) for f in functions
        ])


class GroupEditView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request, group_id):
        group = Group.objects.get(pk=group_id)
        # Protect IT Admin group
        if group.name == 'IT Admin' or getattr(group, 'role_definition', None) and group.role_definition.is_system_role:
            messages.error(request, 'IT Admin group is system-managed and cannot be edited.')
            return redirect(reverse('roles:groups'))
        form = GroupPermissionForm(group=group)
        return render(request, 'roles/group_edit.html', {'group': group, 'form': form})

    def post(self, request, group_id):
        group = Group.objects.get(pk=group_id)
        if group.name == 'IT Admin' or getattr(group, 'role_definition', None) and group.role_definition.is_system_role:
            messages.error(request, 'IT Admin group is system-managed and cannot be edited.')
            return redirect(reverse('roles:groups'))
        form = GroupPermissionForm(request.POST, group=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Permissions updated.')
            return redirect(reverse('roles:groups'))
        return render(request, 'roles/group_edit.html', {'group': group, 'form': form})


class GroupCreateView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        return render(request, 'roles/group_create.html', {})

    def post(self, request):
        name = (request.POST.get('name') or '').strip()
        if not name:
            messages.error(request, 'Group name is required.')
            return render(request, 'roles/group_create.html', {'name': name})
        if Group.objects.filter(name=name).exists():
            messages.error(request, f'Group "{name}" already exists.')
            return render(request, 'roles/group_create.html', {'name': name})
        group = Group.objects.create(name=name)
        # If creating IT Admin, enforce system role and full permissions
        if name == 'IT Admin':
            self._ensure_it_admin_full_permissions()
            messages.success(request, 'IT Admin group created with full permissions.')
            return redirect(reverse('roles:groups'))
        # Merge group and role: create RoleDefinition for the group
        role_def = RoleDefinition.objects.create(group=group, description=f'Custom role for {name}', is_system_role=False)
        messages.success(request, f'Group "{name}" created. Assign function permissions to this role.')
        return redirect(reverse('roles:role_permissions', kwargs={'role_id': role_def.id}))


class GroupDeleteView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request, group_id):
        group = get_object_or_404(Group, pk=group_id)
        # Protect IT Admin group
        if group.name == 'IT Admin' or getattr(group, 'role_definition', None) and group.role_definition.is_system_role:
            messages.error(request, 'IT Admin group is system-managed and cannot be deleted.')
            return redirect(reverse('roles:groups'))
        return render(request, 'roles/group_delete_confirm.html', {'group': group})

    def post(self, request, group_id):
        group = get_object_or_404(Group, pk=group_id)
        if group.name == 'IT Admin' or getattr(group, 'role_definition', None) and group.role_definition.is_system_role:
            messages.error(request, 'IT Admin group is system-managed and cannot be deleted.')
            return redirect(reverse('roles:groups'))
        group.delete()
        messages.success(request, 'Group deleted.')
        return redirect(reverse('roles:groups'))


class UserListView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        users = User.objects.all().order_by('username')
        return render(request, 'roles/users.html', {'users': users})


class UserRoleEditView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request, user_id):
        user = User.objects.get(pk=user_id)
        form = UserRoleForm(user=user)
        return render(request, 'roles/user_roles.html', {'user_obj': user, 'form': form})

    def post(self, request, user_id):
        user = User.objects.get(pk=user_id)
        form = UserRoleForm(request.POST, user=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User roles updated.')
            return redirect(reverse('roles:users'))
        return render(request, 'roles/user_roles.html', {'user_obj': user, 'form': form})


class UserCustomRoleCreateView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        functions = FunctionPermission.objects.filter(is_active=True).order_by('module', 'code')
        # Group by module for easier UI
        modules = {}
        for func in functions:
            modules.setdefault(func.module, []).append(func)
        return render(request, 'roles/user_custom_role.html', {
            'user_obj': user,
            'modules': modules,
        })

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        selected_ids = request.POST.getlist('functions')

        if not name:
            messages.error(request, 'Role name is required.')
            return self.get(request, user_id)
        if Group.objects.filter(name=name).exists():
            messages.error(request, f'A role named "{name}" already exists. Choose a different name.')
            return self.get(request, user_id)
        if not selected_ids:
            messages.error(request, 'Select at least one function permission.')
            return self.get(request, user_id)

        # Create backing group and role definition
        group = Group.objects.create(name=name)
        role = RoleDefinition.objects.create(group=group, description=description, is_system_role=False)

        # Map selected function permissions
        for func_id in selected_ids:
            try:
                func = FunctionPermission.objects.get(pk=func_id, is_active=True)
                RolePermissionMapping.objects.create(role=role, function=func)
            except FunctionPermission.DoesNotExist:
                continue

        # Assign role (group) to the user
        user.groups.add(group)
        messages.success(request, f'Role "{name}" created and assigned to {user.username}.')
        return redirect(reverse('roles:users'))


class UserDeleteView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        # Prevent deletion of current user
        if user.id == request.user.id:
            messages.error(request, 'You cannot delete your own account.')
            return redirect(reverse('roles:users'))
        # Prevent deletion of superusers by non-superusers
        if user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'You cannot delete a superuser account.')
            return redirect(reverse('roles:users'))
        return render(request, 'roles/user_delete_confirm.html', {'user_obj': user})

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        if user.id == request.user.id:
            messages.error(request, 'You cannot delete your own account.')
            return redirect(reverse('roles:users'))
        if user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'You cannot delete a superuser account.')
            return redirect(reverse('roles:users'))
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" has been deleted.')
        return redirect(reverse('roles:users'))


# New: Custom role management views
class RoleListView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        roles = RoleDefinition.objects.select_related('group').all()
        # Preload function mappings per role for display
        mappings = RolePermissionMapping.objects.select_related('function', 'role').filter(role__in=roles)
        perms_by_role = {}
        for m in mappings:
            perms_by_role.setdefault(m.role_id, []).append(m.function)
        return render(request, 'roles/role_list.html', {
            'roles': roles,
            'perms_by_role': perms_by_role,
        })


class RoleCreateView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        return render(request, 'roles/role_create.html', {})

    def post(self, request):
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'Role name is required.')
            return render(request, 'roles/role_create.html', {'name': name, 'description': description})
        
        if Group.objects.filter(name=name).exists():
            messages.error(request, f'Role "{name}" already exists.')
            return render(request, 'roles/role_create.html', {'name': name, 'description': description})
        
        group = Group.objects.create(name=name)
        RoleDefinition.objects.create(group=group, description=description, is_system_role=False)
        messages.success(request, f'Role "{name}" created successfully.')
        return redirect(reverse('roles:role_list'))


class RoleCreateWithPermissionsView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        functions = FunctionPermission.objects.filter(is_active=True).order_by('module', 'code')
        modules = {}
        for func in functions:
            modules.setdefault(func.module, []).append(func)
        return render(request, 'roles/role_create_with_permissions.html', {
            'modules': modules,
        })

    def post(self, request):
        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        selected_ids = request.POST.getlist('functions')

        if not name:
            messages.error(request, 'Role name is required.')
            return self.get(request)
        if Group.objects.filter(name=name).exists():
            messages.error(request, f'Role "{name}" already exists. Pick another name.')
            return self.get(request)
        if not selected_ids:
            messages.error(request, 'Select at least one function permission.')
            return self.get(request)

        group = Group.objects.create(name=name)
        role = RoleDefinition.objects.create(group=group, description=description, is_system_role=False)

        for func_id in selected_ids:
            try:
                func = FunctionPermission.objects.get(pk=func_id, is_active=True)
                RolePermissionMapping.objects.create(role=role, function=func)
            except FunctionPermission.DoesNotExist:
                continue

        messages.success(request, f'Role "{name}" created with selected permissions.')
        return redirect(reverse('roles:role_list'))

class RoleEditView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request, role_id):
        role = get_object_or_404(RoleDefinition, pk=role_id)
        return render(request, 'roles/role_edit.html', {'role': role})

    def post(self, request, role_id):
        role = get_object_or_404(RoleDefinition, pk=role_id)
        
        if role.is_system_role:
            messages.error(request, 'System roles cannot be edited.')
            return redirect(reverse('roles:role_list'))
        
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'Role name is required.')
            return render(request, 'roles/role_edit.html', {'role': role})
        
        if Group.objects.filter(name=name).exclude(pk=role.group.pk).exists():
            messages.error(request, f'Role "{name}" already exists.')
            return render(request, 'roles/role_edit.html', {'role': role})
        
        role.group.name = name
        role.group.save()
        role.description = description
        role.save()
        messages.success(request, f'Role "{name}" updated successfully.')
        return redirect(reverse('roles:role_list'))


class RolePermissionsView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request, role_id):
        role = get_object_or_404(RoleDefinition, pk=role_id)
        functions = FunctionPermission.objects.filter(is_active=True).order_by('module', 'code')
        assigned_func_ids = set(role.permission_mappings.values_list('function_id', flat=True))
        
        # Group functions by module
        modules = {}
        for func in functions:
            if func.module not in modules:
                modules[func.module] = []
            modules[func.module].append({
                'function': func,
                'assigned': func.id in assigned_func_ids
            })
        
        return render(request, 'roles/role_permissions.html', {
            'role': role,
            'modules': modules,
        })

    def post(self, request, role_id):
        role = get_object_or_404(RoleDefinition, pk=role_id)
        selected_ids = request.POST.getlist('functions')
        
        # Clear existing mappings
        RolePermissionMapping.objects.filter(role=role).delete()
        
        # Create new mappings
        for func_id in selected_ids:
            try:
                func = FunctionPermission.objects.get(pk=func_id, is_active=True)
                RolePermissionMapping.objects.create(role=role, function=func)
            except FunctionPermission.DoesNotExist:
                pass
        
        messages.success(request, f'Permissions updated for role "{role.group.name}".')
        return redirect(reverse('roles:role_list'))


class FunctionListView(LoginRequiredMixin, ITAdminOnlyMixin, View):
    def get(self, request):
        functions = FunctionPermission.objects.all().order_by('module', 'code')
        return render(request, 'roles/function_list.html', {'functions': functions})
