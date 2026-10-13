from django.db import models
from django.contrib.auth.models import User
import os

from client.models import Client
from lead.models import Lead


# Create your models here.
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
