from django.db import models
from django.contrib.auth.models import User
from lead.models import Lead
from client.models import Client


# Create your models here.
class Task(models.Model):
    PRIORITY_CHOICES = (
        ('', '---------'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    STATUS_CHOICES = (
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )

    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, related_name='tasks', on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, related_name='assigned_tasks',
                                    on_delete=models.CASCADE,
                                    blank=True,
                                    null=True)
    lead = models.ForeignKey(Lead, related_name='tasks_lead', on_delete=models.CASCADE, null=True, blank=True)
    client = models.ForeignKey(Client, related_name='tasks_client', null=True, blank=True, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='-', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='', blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    due_time = models.TimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class TaskComment(models.Model):
    task = models.ForeignKey(Task, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='task_comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.created_by.username
