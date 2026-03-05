from django.db import models
from django.contrib.auth.models import User
import os


# Create your models here.
class Lead(models.Model):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'

    CHOICES_PRIORITY = (
        (LOW, 'Low'),
        (MEDIUM, 'Medium'),
        (HIGH, 'High'),
        (URGENT, 'Urgent'),
    )

    OPEN = 'open'
    CONTACTED = 'contacted'
    WON = 'won'
    LOST = 'lost'

    CHOICES_STATUS = (
        (OPEN, 'Open'),
        (CONTACTED, 'Contacted'),
        (WON, 'Won'),
        (LOST, 'Lost'),
    )

    reseller = 'reseller'
    direct = 'direct'

    STATUS = (
        (reseller, 'Reseller'),
        (direct, 'Direct'),
    )

    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    status_sale = models.CharField(max_length=255, choices=STATUS, default='', blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    zipcode = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=255, choices=CHOICES_PRIORITY, default=MEDIUM)
    status = models.CharField(max_length=255, choices=CHOICES_STATUS, default='----')
    website = models.URLField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    due_time = models.TimeField(blank=True, null=True)
    converted_to_client = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name='leads', on_delete=models.CASCADE)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.last_name or self.first_name:
            name_parts = [self.last_name, self.first_name]
            name = ' '.join(filter(None, name_parts))
            if self.company:
                return f'{name} - {self.company}'
            return name
        return self.company or 'Unnamed Lead'


# Lead Files
class LeadFile(models.Model):
    lead = models.ForeignKey(Lead, related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='leadfiles')
    created_by = models.ForeignKey(User, related_name='lead_files', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def filename(self):
        """Return just the file's name without the full path."""
        return os.path.basename(self.file.name)

    def __str__(self):
        return self.created_by.username


# Lead Comment
class Comment(models.Model):
    lead = models.ForeignKey(Lead, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='lead_comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.created_by.username
