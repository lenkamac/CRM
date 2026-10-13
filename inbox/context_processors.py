from .models import Email


def unread_emails(request):
    """Unread email count for the sidebar badge."""
    if not request.user.is_authenticated:
        return {}
    return {'inbox_unread_count': Email.objects.filter(owner=request.user, folder=Email.INBOX, is_read=False).count()}
