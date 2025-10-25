from django import forms
from django.contrib.auth.models import Group, Permission, User
from .models import RoleDefinition
from django.contrib.contenttypes.models import ContentType


class GroupPermissionForm(forms.Form):
    view_employee = forms.BooleanField(required=False, label='View employee')
    add_employee = forms.BooleanField(required=False, label='Add employee')
    change_employee = forms.BooleanField(required=False, label='Modify employee')
    delete_employee = forms.BooleanField(required=False, label='Delete employee')

    def __init__(self, *args, group: Group, **kwargs):
        super().__init__(*args, **kwargs)
        self.group = group
        employee_ct = ContentType.objects.get(app_label='employees', model='employee')
        existing = set(group.permissions.filter(content_type=employee_ct).values_list('codename', flat=True))
        for code in ['view_employee', 'add_employee', 'change_employee', 'delete_employee']:
            self.fields[code].initial = code in existing

    def save(self):
        employee_ct = ContentType.objects.get(app_label='employees', model='employee')
        perm_map = {p.codename: p for p in Permission.objects.filter(content_type=employee_ct)}
        selected = [code for code in ['view_employee', 'add_employee', 'change_employee', 'delete_employee'] if self.cleaned_data.get(code)]
        self.group.permissions.remove(*[perm for code, perm in perm_map.items()])
        self.group.permissions.add(*[perm_map[code] for code in selected])


class UserRoleForm(forms.Form):
    roles = forms.ModelMultipleChoiceField(queryset=RoleDefinition.objects.select_related('group').all(), required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, user: User, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        initial_roles = RoleDefinition.objects.filter(group__in=user.groups.all())
        self.fields['roles'].initial = initial_roles

    def save(self):
        # Map selected roles to their backing groups for assignment
        selected_roles = self.cleaned_data['roles']
        groups = [r.group for r in selected_roles]
        self.user.groups.set(groups)
        self.user.save()
