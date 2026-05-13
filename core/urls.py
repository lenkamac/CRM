from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("teams/", views.TeamListView.as_view(), name="teams_manage"),
    path("teams/add/", views.TeamCreateView.as_view(), name="team_add"),
    path("teams/<int:pk>/edit/", views.TeamUpdateView.as_view(), name="team_edit"),
    path("teams/<int:pk>/toggle-active/", views.team_toggle_active, name="team_toggle_active"),
    path("teams/<int:pk>/members/", views.TeamMembersView.as_view(), name="team_members"),
    path("teams/<int:team_pk>/members/add/", views.team_member_add, name="team_member_add"),
    path(
        "teams/<int:team_pk>/members/<int:membership_pk>/toggle-active/",
        views.team_member_toggle_active,
        name="team_member_toggle_active",
    ),
    path(
        "teams/<int:team_pk>/members/<int:membership_pk>/delete/",
        views.team_member_delete,
        name="team_member_delete",
    ),
    path("projects/", views.ProjectListView.as_view(), name="project_list"),
    path("projects/add/", views.ProjectCreateView.as_view(), name="project_add"),
    path("projects/<int:pk>/edit/", views.ProjectUpdateView.as_view(), name="project_edit"),
    path("projects/<int:pk>/delete/", views.ProjectDeleteView.as_view(), name="project_delete"),
    path("teams/<int:pk>/delete/", views.TeamDeleteView.as_view(), name="team_delete"),
    path('teams/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    path("projects/<int:pk>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path("projects/<int:project_pk>/teams/add/", views.project_team_add, name="project_team_add"),
    path(
        "projects/<int:project_pk>/teams/<int:assignment_pk>/remove/",
        views.project_team_remove,
        name="project_team_remove",
    ),
    path("teams/<int:team_pk>/conversations/add/", views.conversation_create, name="conversation_create"),
    path(
        "teams/<int:team_pk>/conversations/<int:conv_pk>/",
        views.ConversationDetailView.as_view(),
        name="conversation_detail",
    ),
    path(
        "teams/<int:team_pk>/conversations/<int:conv_pk>/messages/add/",
        views.message_create,
        name="message_create",
    ),
]