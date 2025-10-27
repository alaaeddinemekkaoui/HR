from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """Authenticate using either username or email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            # Try username first, then email (case-insensitive for email)
            user = UserModel.objects.get(Q(username=username) | Q(email__iexact=username))
        except UserModel.MultipleObjectsReturned:
            # If multiple users have same email (shouldn't happen if email unique), prefer username match
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                return None
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
