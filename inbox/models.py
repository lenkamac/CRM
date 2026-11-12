from django.db import models
from django.contrib.auth.models import User
import os
from email.utils import formataddr

from client.models import Client
from lead.models import Lead
from .crypto import decrypt, encrypt


# Create your models here.
class MailAccount(models.Model):
    """Mailbox connection settings of one CRM user (IMAP for receiving, SMTP for sending)."""
    SSL = 'ssl'
    STARTTLS = 'starttls'

    CHOICES_SMTP_SECURITY = (
        (STARTTLS, 'STARTTLS (usually port 587)'),
        (SSL, 'SSL/TLS (usually port 465)'),
    )

    user = models.OneToOneField(User, related_name='mail_account', on_delete=models.CASCADE)
    email_address = models.EmailField()
    display_name = models.CharField(max_length=255, blank=True)
    username = models.CharField(max_length=255, blank=True, help_text='Login name, if it differs from the email address.')
    password_encrypted = models.TextField(blank=True)
    imap_host = models.CharField(max_length=255)
    imap_port = models.PositiveIntegerField(default=993)
    smtp_host = models.CharField(max_length=255)
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_security = models.CharField(max_length=10, choices=CHOICES_SMTP_SECURITY, default=STARTTLS)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.email_address} ({self.user})'

    @property
    def login(self):
        return self.username or self.email_address

    @property
    def password(self):
        return decrypt(self.password_encrypted)

    @password.setter
    def password(self, value):
        self.password_encrypted = encrypt(value)

    @property
    def is_connected(self):
        return self.is_active and bool(self.password)

    @property
    def from_header(self):
        name = self.display_name or self.user.get_full_name()
        return formataddr((name, self.email_address)) if name else self.email_address


class Email(models.Model):
    INBOX = 'inbox'
    SENT = 'sent'

    CHOICES_FOLDER = (
        (INBOX, 'Inbox'),
        (SENT, 'Sent'),
    )

    owner = models.ForeignKey(User, related_name='emails', on_delete=models.CASCADE)
    folder = models.CharField(max_length=20, choices=CHOICES_FOLDER, default=INBOX)
    imap_uid = models.PositiveBigIntegerField(blank=True, null=True)
    message_id = models.CharField(max_length=998)
    in_reply_to = models.CharField(max_length=998, blank=True)
    sender_name = models.CharField(max_length=255, blank=True)
    sender_email = models.EmailField(blank=True)
    to = models.TextField(blank=True)
    cc = models.TextField(blank=True)
    subject = models.CharField(max_length=998, blank=True)
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    received_at = models.DateTimeField()
    is_read = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    client = models.ForeignKey(Client, related_name='emails', on_delete=models.SET_NULL, null=True, blank=True)
    lead = models.ForeignKey(Lead, related_name='emails', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_at']
        constraints = [
            models.UniqueConstraint(fields=['owner', 'folder', 'message_id'], name='unique_email_per_owner_folder'),
        ]

    def __str__(self):
        return self.subject or '(no subject)'

    @property
    def display_sender(self):
        return self.sender_name or self.sender_email

    @property
    def snippet(self):
        text = ' '.join(self.body_text.split())
        return text[:120] + ('…' if len(text) > 120 else '')


class EmailAttachment(models.Model):
    email = models.ForeignKey(Email, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='inbox_attachments')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, blank=True)
    size = models.PositiveIntegerField(default=0)

    @property
    def basename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return self.filename
