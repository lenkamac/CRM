
from django.db import models

from django.contrib.auth.models import User

from client.models import Client
from lead.models import Lead

class Team(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User,
        related_name="teams_created",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    members = models.ManyToManyField(
        User,
        through="TeamMembership",
        related_name="teams",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class TeamMembership(models.Model):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

    ROLE_CHOICES = (
        (OWNER, "Owner"),
        (ADMIN, "Admin"),
        (MEMBER, "Member"),
    )

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="team_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MEMBER)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("team", "user")
        ordering = ["-joined_at"]

    def __str__(self) -> str:
        return f"{self.team} - {self.user}"


class Project(models.Model):
    PLANNED = "planned"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    DONE = "done"
    CANCELED = "canceled"

    STATUS_CHOICES = (
        (PLANNED, "Planned"),
        (ACTIVE, "Active"),
        (ON_HOLD, "On hold"),
        (DONE, "Done"),
        (CANCELED, "Canceled"),
    )

    PRIORITY_CHOICES = (
        ('', '---------'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PLANNED)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='', blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        User,
        related_name="projects_created",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    teams = models.ManyToManyField(
        Team,
        through="ProjectTeamAssignment",
        related_name="projects",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class ProjectTeamAssignment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="team_assignments")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="project_assignments")

    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "team")
        ordering = ["-assigned_at"]

    def __str__(self) -> str:
        return f"{self.project} -> {self.team}"


class Conversation(models.Model):
    """
    Communication container. A conversation can be:
    - Team-scoped (team set, project empty)
    - Project-scoped (project set, team empty)
    - Both (if you want a "project conversation for a specific team")
    """
    title = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="conversations",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="conversations",
    )

    created_by = models.ForeignKey(
        User,
        related_name="conversations_created",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title or f"Conversation #{self.pk}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_sent")
    body = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.sender} @ {self.created_at:%Y-%m-%d %H:%M}"


class Contacts(models.Model):

    METHOD_CHOICES = (
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('any', 'Any'),
    )

    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='any', blank=True, null=True)

    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=255, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    notes = models.CharField( max_length=400, blank=True, null=True)
    created_by = models.ForeignKey(
        User,
        related_name="contacts_created",
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = [ "last_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"