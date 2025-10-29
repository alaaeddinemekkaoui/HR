from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages


def it_admin_required(function):
    """
    Decorator to check if user is IT Admin or superuser.
    Only IT Admins can manage signature system.
    """
    def check_it_admin(user):
        if user.is_superuser:
            return True
        return user.groups.filter(name='IT Admin').exists()
    
    decorated_function = user_passes_test(
        check_it_admin,
        login_url='/',
        redirect_field_name=None
    )(function)
    
    def wrapper(request, *args, **kwargs):
        if not check_it_admin(request.user):
            messages.error(request, 'Only IT Admins can access this feature.')
            return redirect('signatures:my_requests')
        return decorated_function(request, *args, **kwargs)
    
    return wrapper


def signature_permission_required(permission_code):
    """
    Decorator to check if user has specific signature permission.
    
    Args:
        permission_code: e.g., 'signature.sign', 'signature.admin'
    """
    def decorator(function):
        def wrapper(request, *args, **kwargs):
            # Superuser has all permissions
            if request.user.is_superuser:
                return function(request, *args, **kwargs)
            
            # Check if user has the permission through their role
            from apps.roles.models import RoleDefinition, FunctionPermission, RolePermissionMapping
            
            try:
                # Get user's role
                if not hasattr(request.user, 'employee_profile') or not request.user.employee_profile:
                    messages.error(request, 'You do not have permission to access this feature.')
                    return redirect('signatures:my_requests')
                
                # Get user's groups (roles)
                user_groups = request.user.groups.all()
                
                # Check if any of user's roles have this permission
                has_permission = RolePermissionMapping.objects.filter(
                    role__group__in=user_groups,
                    function__code=permission_code
                ).exists()
                
                if has_permission:
                    return function(request, *args, **kwargs)
                else:
                    messages.error(request, 'You do not have permission to access this feature.')
                    return redirect('signatures:my_requests')
                    
            except Exception as e:
                messages.error(request, 'Error checking permissions.')
                return redirect('signatures:my_requests')
        
        return wrapper
    return decorator
