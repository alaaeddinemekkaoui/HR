from django.conf import settings
from django.shortcuts import redirect


EXEMPT_PATH_PREFIXES = (
    # login/logout paths
    getattr(settings, 'LOGIN_URL', '/accounts/login/'),
    getattr(settings, 'LOGOUT_REDIRECT_URL', '/accounts/login/'),
    # admin and static files
    '/admin/',
    '/static/',
    '/media/',
    '/favicon.ico',
)


class LoginRequiredMiddleware:
    """Redirect anonymous users to the login page.

    This middleware intentionally keeps the whitelist small. If you need to
    allow additional open endpoints (health checks, webhooks), set
    LOGIN_EXEMPT_PATHS in Django settings to a list of path prefixes.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        extras = getattr(settings, 'LOGIN_EXEMPT_PATHS', [])
        # Normalize to prefixes
        self.exempt_prefixes = list(EXEMPT_PATH_PREFIXES) + list(extras)

    def __call__(self, request):
        path = request.path_info
        # Allow if path starts with any exempt prefix
        for p in self.exempt_prefixes:
            if path.startswith(p):
                return self.get_response(request)

        # If user not authenticated, redirect to login with next
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')
            # Preserve next parameter
            return redirect(f"{login_url}?next={request.path}")

        return self.get_response(request)
