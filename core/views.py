from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView

from .forms import ProjectTeamAddForm, TeamForm, TeamMemberAddForm, ProjectForm
from .models import Project, ProjectTeamAssignment, Team, TeamMembership

# Create your views here.
def index(request):
    return render(request, 'core/index.html')


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "core/projects/project_form.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Project updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:project_detail", kwargs={"pk": self.object.pk})


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = "core/projects/project_confirm_delete.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Project deleted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:project_list")

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "core/projects/project_list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user).order_by("-created_at")


class TeamListView(LoginRequiredMixin, ListView):
    model = Team
    template_name = "core/teams/manage_teams.html"
    context_object_name = "teams"

    def get_queryset(self):
        return Team.objects.filter(created_by=self.request.user).order_by("name")


class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = "core/teams/team_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Team created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:teams_manage")


class TeamUpdateView(LoginRequiredMixin, UpdateView):
    model = Team
    form_class = TeamForm
    template_name = "core/teams/team_form.html"

    def get_queryset(self):
        return Team.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Team updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:teams_manage")

class TeamDeleteView(LoginRequiredMixin, DeleteView):
    model = Team
    template_name = "core/teams/team_confirm_delete.html"
    context_object_name = "team"

    def get_queryset(self):
        return Team.objects.filter(created_by=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Team deleted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:teams_manage")


@login_required
def team_toggle_active(request, pk: int):
    if request.method != "POST":
        raise Http404()

    team = get_object_or_404(Team, pk=pk, created_by=request.user)
    team.is_active = not team.is_active
    team.save(update_fields=["is_active"])
    messages.success(request, f"Team {'activated' if team.is_active else 'deactivated'}.")
    return redirect("core:teams_manage")


class TeamMembersView(LoginRequiredMixin, DetailView):
    model = Team
    template_name = "core/teams/team_members.html"
    context_object_name = "team"

    def get_queryset(self):
        return Team.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["add_form"] = TeamMemberAddForm()
        ctx["memberships"] = (
            TeamMembership.objects.select_related("user")
            .filter(team=self.object)
            .order_by("-is_active", "user__username")
        )
        return ctx


@login_required
@transaction.atomic
def team_member_add(request, team_pk: int):
    if request.method != "POST":
        raise Http404()

    team = get_object_or_404(Team, pk=team_pk, created_by=request.user)
    form = TeamMemberAddForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please correct the errors and try again.")
        return redirect("core:team_members", pk=team.pk)

    user = form.cleaned_data["user"]
    role = form.cleaned_data["role"]

    membership, created = TeamMembership.objects.get_or_create(
        team=team,
        user=user,
        defaults={"role": role, "is_active": True},
    )
    if not created:
        membership.role = role
        membership.is_active = True
        membership.save(update_fields=["role", "is_active"])

    messages.success(request, "Member added (or re-activated).")
    return redirect("core:team_members", pk=team.pk)


@login_required
def team_member_toggle_active(request, team_pk: int, membership_pk: int):
    if request.method != "POST":
        raise Http404()

    team = get_object_or_404(Team, pk=team_pk, created_by=request.user)
    membership = get_object_or_404(TeamMembership, pk=membership_pk, team=team)
    membership.is_active = not membership.is_active
    membership.save(update_fields=["is_active"])
    messages.success(request, f"Membership {'activated' if membership.is_active else 'deactivated'}.")
    return redirect("core:team_members", pk=team.pk)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "core/projects/project_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Project created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:project_detail", kwargs={"pk": self.object.pk})

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = "core/projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx["assigned_teams"] = (
            ProjectTeamAssignment.objects.select_related("team")
            .filter(project=self.object, is_active=True)
            .order_by("-assigned_at")
        )

        add_form = ProjectTeamAddForm()
        add_form.fields["team"].queryset = Team.objects.filter(
            created_by=self.request.user,
            is_active=True,
        ).order_by("name")
        ctx["add_team_form"] = add_form
        return ctx


@login_required
@transaction.atomic
def project_team_add(request, project_pk: int):
    if request.method != "POST":
        raise Http404()

    project = get_object_or_404(Project, pk=project_pk, created_by=request.user)
    form = ProjectTeamAddForm(request.POST)
    form.fields["team"].queryset = Team.objects.filter(created_by=request.user, is_active=True)

    if not form.is_valid():
        messages.error(request, "Please select a team.")
        return redirect("core:project_detail", pk=project.pk)

    team = form.cleaned_data["team"]

    assignment, created = ProjectTeamAssignment.objects.get_or_create(
        project=project,
        team=team,
        defaults={"is_active": True},
    )
    if not created and assignment.is_active is False:
        assignment.is_active = True
        assignment.save(update_fields=["is_active"])

    messages.success(request, "Team assigned to project.")
    return redirect("core:project_detail", pk=project.pk)


@login_required
def project_team_remove(request, project_pk: int, assignment_pk: int):
    if request.method != "POST":
        raise Http404()

    project = get_object_or_404(Project, pk=project_pk, created_by=request.user)
    assignment = get_object_or_404(ProjectTeamAssignment, pk=assignment_pk, project=project)
    assignment.is_active = False
    assignment.save(update_fields=["is_active"])
    messages.success(request, "Team unassigned (deactivated).")
    return redirect("core:project_detail", pk=project.pk)