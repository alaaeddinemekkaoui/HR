from django.db.utils import ProgrammingError, OperationalError
from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {}
    # Be defensive: during initial deploy before migrations, the table may not exist yet.
    try:
        unread_qs = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
        return {
            'notifications_unread': unread_qs[:5],
            'notifications_unread_count': unread_qs.count(),
        }
    except (ProgrammingError, OperationalError):
        # Notifications table not ready yet (migrations pending)
        return {
            'notifications_unread': [],
            'notifications_unread_count': 0,
        }
