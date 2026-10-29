"""Mailbox integration: fetch messages over IMAP and send over SMTP.

Works with any provider (Gmail, Yahoo, iCloud, Seznam, ...). Credentials and
servers come from the MAIL_* variables in .env, see CrmSys/settings.py.
For Gmail use a Google App Password, not your normal password.
"""
import email
import imaplib
import re
from email.header import decode_header, make_header
from email.utils import getaddresses, make_msgid, parseaddr, parsedate_to_datetime

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models import Max
from django.utils import timezone

from client.models import Client
from lead.models import Lead
from .models import Email, EmailAttachment

INITIAL_FETCH_LIMIT = 50


class MailNotConfigured(Exception):
    pass


def _check_config():
    if not settings.MAIL_USER or not settings.MAIL_PASSWORD:
        raise MailNotConfigured('Email is not configured. Add MAIL_USER and MAIL_PASSWORD to your .env file.')


def _decode(value):
    if not value:
        return ''
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


def _decode_payload(part):
    payload = part.get_payload(decode=True) or b''
    charset = part.get_content_charset() or 'utf-8'
    try:
        return payload.decode(charset, errors='replace')
    except LookupError:
        return payload.decode('utf-8', errors='replace')


def _parse_date(value):
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_default_timezone())
    return dt


def _format_addresses(value):
    pairs = getaddresses([_decode(value)]) if value else []
    return ', '.join(addr for _, addr in pairs if addr)


def _parse_message(msg):
    """Return (text, html, attachments) where attachments is a list of (filename, content_type, bytes)."""
    text, html, attachments = '', '', []
    for part in msg.walk():
        if part.is_multipart():
            continue
        content_type = part.get_content_type()
        filename = part.get_filename()
        disposition = (part.get('Content-Disposition') or '').lower()
        if filename or 'attachment' in disposition:
            data = part.get_payload(decode=True)
            if data:
                attachments.append((_decode(filename) or 'attachment', content_type, data))
        elif content_type == 'text/plain' and not text:
            text = _decode_payload(part)
        elif content_type == 'text/html' and not html:
            html = _decode_payload(part)
    return text, html, attachments


def _match_contacts(user, address):
    """Link an email address to the user's client and lead records."""
    if not address:
        return None, None
    client = Client.objects.filter(created_by=user, email__iexact=address).first()
    lead = Lead.objects.filter(created_by=user, email__iexact=address).first()
    return client, lead


def _connect(readonly=True):
    imap = imaplib.IMAP4_SSL(settings.MAIL_IMAP_HOST, settings.MAIL_IMAP_PORT)
    imap.login(settings.MAIL_USER, settings.MAIL_PASSWORD)
    imap.select('INBOX', readonly=readonly)
    return imap


def _logout(imap):
    try:
        imap.logout()
    except Exception:
        pass


def _is_seen(fetch_response):
    """Return True if the \\Seen flag is in a FETCH response line."""
    return b'\\Seen' in imaplib.ParseFlags(fetch_response)


def _sync_read_flags(imap, user):
    """Copy the read/unread state of already stored emails from the mailbox to the CRM."""
    known = dict(
        Email.objects.filter(owner=user, folder=Email.INBOX, imap_uid__isnull=False).values_list('imap_uid', 'is_read')
    )
    if not known:
        return
    _, data = imap.uid('fetch', f'{min(known)}:{max(known)}', '(FLAGS)')
    read_uids, unread_uids = [], []
    for item in data or []:
        line = item[0] if isinstance(item, tuple) else item
        if not isinstance(line, bytes):
            continue
        match = re.search(rb'UID (\d+)', line)
        if not match or int(match.group(1)) not in known:
            continue
        uid, seen = int(match.group(1)), _is_seen(line)
        if seen != known[uid]:
            (read_uids if seen else unread_uids).append(uid)
    base = Email.objects.filter(owner=user, folder=Email.INBOX)
    if read_uids:
        base.filter(imap_uid__in=read_uids).update(is_read=True)
    if unread_uids:
        base.filter(imap_uid__in=unread_uids).update(is_read=False)


def set_read_flag(emails, is_read):
    """Mark the given CRM emails as read/unread in the mailbox too."""
    uids = [str(m.imap_uid) for m in emails if m.folder == Email.INBOX and m.imap_uid]
    if not uids:
        return
    _check_config()
    imap = _connect(readonly=False)
    try:
        imap.uid('store', ','.join(uids), '+FLAGS' if is_read else '-FLAGS', '(\\Seen)')
    finally:
        _logout(imap)


def fetch_emails(user, limit=INITIAL_FETCH_LIMIT):
    """Download new messages from the mailbox INBOX. Returns the number of new emails stored."""
    _check_config()

    last_uid = Email.objects.filter(owner=user, folder=Email.INBOX).aggregate(m=Max('imap_uid'))['m']

    imap = _connect()
    try:
        _sync_read_flags(imap, user)

        if last_uid:
            _, data = imap.uid('search', None, f'UID {last_uid + 1}:*')
        else:
            _, data = imap.uid('search', None, 'ALL')
        uids = [int(u) for u in data[0].split()]
        # "n:*" always returns the newest message, even if it is older than n
        uids = [u for u in uids if not last_uid or u > last_uid]
        if not last_uid:
            uids = uids[-limit:]

        created = 0
        for uid in uids:
            # BODY.PEEK keeps the message unread in Gmail
            _, msg_data = imap.uid('fetch', str(uid), '(FLAGS BODY.PEEK[])')
            if not msg_data or not isinstance(msg_data[0], tuple):
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            # FLAGS may come before or after the body in the response
            is_read = any(_is_seen(p[0] if isinstance(p, tuple) else p) for p in msg_data if isinstance(p, (bytes, tuple)))

            message_id = (msg.get('Message-ID') or '').strip() or f'<imap-uid-{uid}@{settings.MAIL_IMAP_HOST}>'
            if Email.objects.filter(owner=user, folder=Email.INBOX, message_id=message_id).exists():
                continue

            sender_name, sender_email = parseaddr(_decode(msg.get('From')))
            text, html, attachments = _parse_message(msg)
            client, lead = _match_contacts(user, sender_email)

            mail = Email.objects.create(
                owner=user,
                folder=Email.INBOX,
                imap_uid=uid,
                message_id=message_id,
                in_reply_to=(msg.get('In-Reply-To') or '').strip(),
                sender_name=sender_name,
                sender_email=sender_email,
                to=_format_addresses(msg.get('To')),
                cc=_format_addresses(msg.get('Cc')),
                subject=_decode(msg.get('Subject')),
                body_text=text,
                body_html=html,
                received_at=_parse_date(msg.get('Date')),
                is_read=is_read,
                client=client,
                lead=lead,
            )
            for filename, content_type, data in attachments:
                attachment = EmailAttachment(email=mail, filename=filename, content_type=content_type, size=len(data))
                attachment.file.save(filename, ContentFile(data), save=True)
            created += 1
        return created
    finally:
        _logout(imap)


def send_email(user, to, subject, body, cc='', attachments=None, reply_to_email=None):
    """Send an email through the SMTP server and store a copy in the Sent folder."""
    _check_config()

    to_list = [a for _, a in getaddresses([to]) if a]
    cc_list = [a for _, a in getaddresses([cc]) if a]
    message_id = make_msgid(domain=settings.MAIL_USER.split('@')[-1])
    headers = {'Message-ID': message_id}
    if reply_to_email:
        headers['In-Reply-To'] = reply_to_email.message_id
        headers['References'] = reply_to_email.message_id

    connection = get_connection(
        backend='django.core.mail.backends.smtp.EmailBackend',
        host=settings.MAIL_SMTP_HOST,
        port=settings.MAIL_SMTP_PORT,
        username=settings.MAIL_USER,
        password=settings.MAIL_PASSWORD,
        use_ssl=settings.MAIL_SMTP_SSL,
        use_tls=not settings.MAIL_SMTP_SSL,
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=settings.MAIL_USER,
        to=to_list,
        cc=cc_list,
        headers=headers,
        connection=connection,
    )
    attachments = attachments or []
    for f in attachments:
        f.seek(0)
        message.attach(f.name, f.read(), getattr(f, 'content_type', None))
    message.send()

    first_recipient = to_list[0] if to_list else ''
    client, lead = _match_contacts(user, first_recipient)
    if reply_to_email:
        client = client or reply_to_email.client
        lead = lead or reply_to_email.lead

    sent = Email.objects.create(
        owner=user,
        folder=Email.SENT,
        message_id=message_id,
        in_reply_to=reply_to_email.message_id if reply_to_email else '',
        sender_name=user.get_full_name() or user.username,
        sender_email=settings.MAIL_USER,
        to=', '.join(to_list),
        cc=', '.join(cc_list),
        subject=subject,
        body_text=body,
        received_at=timezone.now(),
        is_read=True,
        client=client,
        lead=lead,
    )
    for f in attachments:
        f.seek(0)
        data = f.read()
        attachment = EmailAttachment(email=sent, filename=f.name, content_type=getattr(f, 'content_type', '') or '', size=len(data))
        attachment.file.save(f.name, ContentFile(data), save=True)
    return sent
