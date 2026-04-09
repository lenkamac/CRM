from django.contrib import admin

# Register your models here.
from .models import (
    Team,
    TeamMembership,
    Project,
    ProjectTeamAssignment,
    Conversation,
    Message,
)


# ... existing code ...


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_by", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("team", "user", "role", "is_active", "joined_at")
    list_filter = ("role", "is_active", "team")
    search_fields = ("team__name", "user__username")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "is_active", "client", "lead", "created_by", "created_at")
    list_filter = ("status", "is_active", "client")
    search_fields = ("name",)


@admin.register(ProjectTeamAssignment)
class ProjectTeamAssignmentAdmin(admin.ModelAdmin):
    list_display = ("project", "team", "is_active", "assigned_at")
    list_filter = ("is_active", "team")
    search_fields = ("project__name", "team__name")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "team", "project", "is_active", "created_by", "created_at")
    list_filter = ("is_active", "team")
    search_fields = ("title",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "created_at")
    search_fields = ("sender__username", "body")