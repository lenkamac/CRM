import imaplib
import smtplib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ComposeEmailForm, LinkContactForm
from .gmail_service import MailNotConfigured, fetch_emails, send_email
from .models import Email, EmailAttachment


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
    })


# Email detail page
@login_required
def inbox_detail(request, pk):
    mail = get_object_or_404(Email, pk=pk, owner=request.user)
    if not mail.is_read:
        mail.is_read = True
        mail.save(update_fields=['is_read'])

    thread = Email.objects.filter(owner=request.user).filter(
        Q(in_reply_to=mail.message_id) | Q(message_id=mail.in_reply_to)
    ).exclude(pk=mail.pk) if mail.message_id else Email.objects.none()

    link_form = LinkContactForm(user=request.user, initial={'client': mail.client, 'lead': mail.lead})

    return render(request, 'inbox/inbox_detail.html', {
        'mail': mail,
        'thread': thread,
        'link_form': link_form,
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


# Download new emails from Gmail
@login_required
@require_POST
def inbox_sync(request):
    try:
        count = fetch_emails(request.user)
    except MailNotConfigured as e:
        messages.error(request, str(e))
    except (imaplib.IMAP4.error, OSError) as e:
        messages.error(request, f'Sync with Gmail failed: {e}')
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
    return _redirect_next(request)


@login_required
@require_POST
def inbox_toggle_star(request, pk):
    mail = get_object_or_404(Email, pk=pk, owner=request.user)
    mail.is_starred = not mail.is_starred
    mail.save(update_fields=['is_starred'])
    return _redirect_next(request)


# Removes the email from the CRM only, the message stays in Gmail
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
    elif action == 'read':
        emails.update(is_read=True)
    elif action == 'unread':
        emails.update(is_read=False)
    elif action == 'delete':
        for attachment in EmailAttachment.objects.filter(email__in=emails):
            attachment.file.delete(save=False)
        count = emails.count()
        emails.delete()
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
