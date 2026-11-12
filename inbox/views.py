import imaplib
import smtplib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_POST

from .contact_extract import original_contact
from .forms import MAIL_PROVIDERS, ComposeEmailForm, LinkContactForm, MailAccountForm
from .gmail_service import (MailNotConfigured, check_connection, fetch_emails, mailbox_address, send_email,
                            set_read_flag)
from .models import Email, EmailAttachment, MailAccount


def _push_read_flag(request, emails, is_read):
    """Mirror a read/unread change to the mailbox; the CRM change is kept even if this fails."""
    try:
        set_read_flag(request.user, emails, is_read)
    except MailNotConfigured:
        pass  # mailbox disconnected - the change is kept in the CRM only
    except (imaplib.IMAP4.error, OSError) as e:
        messages.warning(request, f'Could not update the read status in your mailbox: {e}')


def _redirect_next(request):
    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('inbox:list')


# Create your views here.
# Inbox list (inbox / unread / starred / sent)
@login_required
def inbox_list(request):
    folder = request.GET.get('folder', 'inbox')
    emails = Email.objects.filter(owner=request.user).select_related('client', 'lead').prefetch_related('attachments')

    if folder == 'sent':
        emails = emails.filter(folder=Email.SENT)
    elif folder == 'unread':
        emails = emails.filter(folder=Email.INBOX, is_read=False)
    elif folder == 'starred':
        emails = emails.filter(is_starred=True)
    else:
        folder = 'inbox'
        emails = emails.filter(folder=Email.INBOX)

    query = request.GET.get('q')
    if query:
        emails = emails.filter(
            Q(subject__icontains=query) |
            Q(sender_name__icontains=query) |
            Q(sender_email__icontains=query) |
            Q(to__icontains=query) |
            Q(body_text__icontains=query)
        )

    paginator = Paginator(emails, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'inbox/inbox_list.html', {
        'page_obj': page_obj,
        'emails': page_obj.object_list,
        'is_paginated': page_obj.has_other_pages(),
        'folder': folder,
        'mail_account': MailAccount.objects.filter(user=request.user).first(),
    })


# Email detail page
@login_required
def inbox_detail(request, pk):
    mail = get_object_or_404(Email, pk=pk, owner=request.user)
    if not mail.is_read:
        mail.is_read = True
        mail.save(update_fields=['is_read'])
        _push_read_flag(request, [mail], True)

    thread = Email.objects.filter(owner=request.user).filter(
        Q(in_reply_to=mail.message_id) | Q(message_id=mail.in_reply_to)
    ).exclude(pk=mail.pk) if mail.message_id else Email.objects.none()

    link_form = LinkContactForm(user=request.user, initial={'client': mail.client, 'lead': mail.lead})

    # Prefill for "Create lead/client": for forwarded emails this is the original sender
    contact = original_contact(mail, exclude=(mailbox_address(request.user), request.user.email))
    prefill = urlencode({k: contact[k] for k in ('email', 'first_name', 'last_name', 'phone') if contact[k]})

    return render(request, 'inbox/inbox_detail.html', {
        'mail': mail,
        'thread': thread,
        'link_form': link_form,
        'contact': contact,
        'contact_prefill': prefill,
    })


# Compose a new email (optionally prefilled with ?to=)
@login_required
def inbox_compose(request):
    if request.method == 'POST':
        form = ComposeEmailForm(request.POST, request.FILES)
        if form.is_valid():
            if _send(request, form):
                return redirect(f"{reverse('inbox:list')}?folder=sent")
    else:
        form = ComposeEmailForm(initial={'to': request.GET.get('to', '')})

    return render(request, 'inbox/inbox_compose.html', {'form': form, 'title': 'New email'})


# Reply to an email
@login_required
def inbox_reply(request, pk):
    original = get_object_or_404(Email, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = ComposeEmailForm(request.POST, request.FILES)
        if form.is_valid():
            if _send(request, form, reply_to_email=original):
                return redirect('inbox:detail', pk=original.pk)
    else:
        subject = original.subject or ''
        if not subject.lower().startswith('re:'):
            subject = f'Re: {subject}'
        quoted = '\n'.join(f'> {line}' for line in original.body_text.splitlines())
        reply_to = original.sender_email if original.folder == Email.INBOX else original.to
        form = ComposeEmailForm(initial={
            'to': reply_to,
            'subject': subject,
            'body': f'\n\nOn {original.received_at:%d.%m.%Y %H:%M}, {original.display_sender} wrote:\n{quoted}',
        })

    return render(request, 'inbox/inbox_compose.html', {'form': form, 'original': original, 'title': 'Reply'})


def _send(request, form, reply_to_email=None):
    try:
        send_email(
            request.user,
            to=form.cleaned_data['to'],
            cc=form.cleaned_data['cc'],
            subject=form.cleaned_data['subject'],
            body=form.cleaned_data['body'],
            attachments=form.cleaned_data['attachments'],
            reply_to_email=reply_to_email,
        )
    except MailNotConfigured as e:
        messages.error(request, str(e))
        return False
    except (smtplib.SMTPException, OSError) as e:
        messages.error(request, f'Sending failed: {e}')
        return False
    messages.success(request, 'Email was sent.')
    return True


# Download new emails from the mailbox
@login_required
@require_POST
def inbox_sync(request):
    try:
        count = fetch_emails(request.user)
    except MailNotConfigured as e:
        messages.error(request, str(e))
    except (imaplib.IMAP4.error, OSError) as e:
        messages.error(request, f'Sync with your mailbox failed: {e}')
    else:
        if count:
            messages.success(request, f'{count} new email{"s" if count != 1 else ""} fetched.')
        else:
            messages.info(request, 'No new emails.')
    return redirect('inbox:list')


@login_required
@require_POST
def inbox_toggle_read(request, pk):
    mail = get_object_or_404(Email, pk=pk, owner=request.user)
    mail.is_read = not mail.is_read
    mail.save(update_fields=['is_read'])
    _push_read_flag(request, [mail], mail.is_read)
    return _redirect_next(request)


@login_required
@require_POST
def inbox_toggle_star(request, pk):
    mail = get_object_or_404(Email, pk=pk, owner=request.user)
    mail.is_starred = not mail.is_starred
    mail.save(update_fields=['is_starred'])
    return _redirect_next(request)


# Removes the email from the CRM only, the message stays in the mailbox
@login_required
@require_POST
def inbox_delete(request, pk):
    mail = get_object_or_404(Email, pk=pk, owner=request.user)
    for attachment in mail.attachments.all():
        attachment.file.delete(save=False)
    mail.delete()
    messages.success(request, 'Email was removed from the CRM.')
    return redirect('inbox:list')


@login_required
@require_POST
def inbox_bulk_action(request):
    ids = request.POST.getlist('email_ids')
    action = request.POST.get('action')
    emails = Email.objects.filter(owner=request.user, pk__in=ids)

    if not ids:
        messages.warning(request, 'No emails selected.')
    elif action in ('read', 'unread'):
        is_read = action == 'read'
        emails.update(is_read=is_read)
        _push_read_flag(request, emails, is_read)
    elif action == 'delete':
        count = _delete_emails(emails)
        messages.success(request, f'{count} email(s) removed from the CRM.')

    return _redirect_next(request)


# Link an email to a client / lead
@login_required
@require_POST
def inbox_link_contact(request, pk):
    mail = get_object_or_404(Email, pk=pk, owner=request.user)
    form = LinkContactForm(request.POST, user=request.user)
    if form.is_valid():
        mail.client = form.cleaned_data['client']
        mail.lead = form.cleaned_data['lead']
        mail.save(update_fields=['client', 'lead'])
        messages.success(request, 'Email links were updated.')
    return redirect('inbox:detail', pk=mail.pk)


@login_required
def inbox_attachment(request, pk):
    attachment = get_object_or_404(EmailAttachment, pk=pk, email__owner=request.user)
    return FileResponse(attachment.file.open('rb'), as_attachment=True, filename=attachment.filename)


def _delete_emails(emails):
    for attachment in EmailAttachment.objects.filter(email__in=emails):
        attachment.file.delete(save=False)
    count = emails.count()
    emails.delete()
    return count


# Mailbox settings of the logged-in user
@login_required
def inbox_settings(request):
    account = MailAccount.objects.filter(user=request.user).first()
    old_mailbox = (account.email_address.lower(), account.imap_host.lower()) if account else None

    if request.method == 'POST':
        form = MailAccountForm(request.POST, instance=account)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            password = form.cleaned_data['password']
            errors = check_connection(account, password) if form.cleaned_data['test_connection'] else []
            if errors:
                for error in errors:
                    form.add_error(None, error)
            else:
                # Another mailbox has different IMAP UIDs - stored emails stay, but are no longer synced
                if old_mailbox and old_mailbox != (account.email_address.lower(), account.imap_host.lower()):
                    Email.objects.filter(owner=request.user, folder=Email.INBOX).update(imap_uid=None)
                account.password = password
                account.is_active = True
                account.save()
                messages.success(request, f'Mailbox {account.email_address} is connected.')
                return redirect('inbox:settings')
    else:
        form = MailAccountForm(instance=account, initial={'display_name': request.user.get_full_name()} if not account else None)

    return render(request, 'inbox/inbox_settings.html', {
        'form': form,
        # Re-read so a failed attempt does not show unsaved values as the current connection
        'account': MailAccount.objects.filter(user=request.user).first(),
        'providers': MAIL_PROVIDERS,
    })


# Disconnect ("log out") the mailbox: the password is forgotten, nothing can be sent or synced
@login_required
@require_POST
def inbox_disconnect(request):
    account = MailAccount.objects.filter(user=request.user).first()
    if account:
        account.password_encrypted = ''
        account.is_active = False
        account.save(update_fields=['password_encrypted', 'is_active', 'updated_at'])
    if request.POST.get('remove_emails'):
        count = _delete_emails(Email.objects.filter(owner=request.user))
        messages.success(request, f'Mailbox disconnected and {count} email(s) removed from the CRM.')
    else:
        messages.success(request, 'Mailbox disconnected. Emails can no longer be sent or synced until you connect again.')
    return redirect('inbox:settings')
