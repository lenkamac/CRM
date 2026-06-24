from django import forms
from django.contrib.auth.models import User

from .models import Team, TeamMembership, ProjectTeamAssignment
from .models import Project, Conversation, Message
from .models import Contacts


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
    start_date = forms.DateField(required=False,
                                 input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
                                 widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control', 'placeholder': 'dd.mm.yyyy'}))
    end_date = forms.DateField(required=False,
                               input_formats=['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d'],
                               widget=forms.DateInput(format='%d.%m.%Y', attrs={'class': 'form-control', 'placeholder': 'dd.mm.yyyy'}))
    team = forms.ModelChoiceField(
        queryset=Team.objects.none(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        empty_label="— No team —",
    )

    class Meta:
        model = Project
        fields = ["name", "description", "status", "priority","start_date","end_date","is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Project name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Project description"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        def clean(self):
            cleaned_data = super().clean()
            start_date = cleaned_data.get('start_date')
            end_date = cleaned_data.get('end_date')

            if start_date and end_date and start_date > end_date:
                self.add_error('end_date', 'End date must be after start date')

            return cleaned_data


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


# Contacts
class ContactAddForm(forms.ModelForm):
    class Meta:
        model = Contacts
        fields = ["first_name", "last_name", "email", "phone_number", "method", "company", "job_title", "notes"]

        def  clean(self):
            cleaned_data = super().clean()
            first_name = cleaned_data.get('first_name', '').strip()
            last_name = cleaned_data.get('last_name', '').strip()

            if first_name or last_name:
                qs = Contacts.objects.filter(
                    first_name__iexact=first_name,
                    last_name__iexact=last_name
                )
                if self.instance.pk:
                    qs = qs.exclude(pk=self.instance.pk)
                if qs.exists():
                    name = f'{first_name} {last_name}'.strip()
                    raise forms.ValidationError(
                        f'A contact named "{name}" already exists in the list.'
                    )
            return cleaned_data

