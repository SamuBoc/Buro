from .models import Notification

def notifications_count(request):
    if request.user.is_authenticated:
        qs = Notification.objects.filter(
            recipient_user=request.user,
            is_read=False,
        ).order_by('-created_at')
        return {
            'unread_notifications_count': qs.count(),
            'recent_notifications': qs[:10],
        }
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }