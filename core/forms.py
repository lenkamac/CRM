from django import forms
from django.contrib.auth.models import User

from .models import Team, TeamMembership, ProjectTeamAssignment
from .models import Project, Conversation, Message


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ["name", "is_active"]


class TeamMemberAddForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    role = forms.ChoiceField(choices=TeamMembership.ROLE_CHOICES)


class ProjectTeamAddForm(forms.Form):
    team = forms.ModelChoiceField(queryset=Team.objects.filter(is_active=True))


class ProjectTeamAssignmentForm(forms.ModelForm):
    """Not required for the UI below, but handy if you later want an edit screen."""

    class Meta:
        model = ProjectTeamAssignment
        fields = ["is_active"]

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "status",
            "is_active",
        ]


class ConversationForm(forms.ModelForm):
    class Meta:
        model = Conversation
        fields = ["title"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Conversation title (optional)"}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Write a message…"}),
        }