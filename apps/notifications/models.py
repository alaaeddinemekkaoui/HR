from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    CATEGORY_CHOICES = [
        ('leave_request', 'Leave Request'),
        ('leave_update', 'Leave Update'),
        ('general', 'General'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications_sent')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    title = models.CharField(max_length=150)
    message = models.TextField(blank=True)
    url = models.CharField(max_length=255, blank=True)  # relative URL to navigate on click
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.title}"