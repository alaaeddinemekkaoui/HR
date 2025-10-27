from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import Notification


class NotificationListView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        return render(request, 'notifications/list.html', {'notifications': qs})


class NotificationMarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications:list')


class NotificationClearAllView(LoginRequiredMixin, View):
    def post(self, request):
        count = Notification.objects.filter(recipient=request.user).count()
        Notification.objects.filter(recipient=request.user).delete()
        messages.success(request, f'{count} notification(s) cleared.')
        return redirect('notifications:list')


class NotificationGoView(LoginRequiredMixin, View):
    """Mark a notification as read and redirect to its target URL."""
    def get(self, request, pk):
        n = get_object_or_404(Notification, pk=pk, recipient=request.user)
        if not n.is_read:
            Notification.objects.filter(pk=n.pk, is_read=False).update(is_read=True)
        target = n.url or reverse('notifications:list')
        return redirect(target)
