from .models import Email, MailAccount


def unread_emails(request):
    """Unread email count for the sidebar badge."""
    if not request.user.is_authenticated:
        return {}
    account = MailAccount.objects.filter(user=request.user).first()
    if not (account and account.is_connected):
        return {}  # no badge while the mailbox is disconnected
    return {'inbox_unread_count': Email.objects.filter(owner=request.user, folder=Email.INBOX, is_read=False).count()}
