from django import forms
from django.forms.widgets import TimeInput

from .models import Task, TaskComment


class Time24HourInput(TimeInput):
    input_type = 'text'
    format = '%H:%M'

    def __init__(self, attrs=None, format=None):
        default_attrs = {'placeholder': 'HH:MM (24-hour format)', 'pattern': '[0-9]{2}:[0-9]{2}'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, format=format or self.format)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'lead', 'client', 'assigned_to','due_date', 'due_time']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'text', 'class': 'form-control', 'placeholder': 'dd.mm.yyyy', 'autocomplete': 'off'}),
            'due_time': Time24HourInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'lead': forms.Select(attrs={'class': 'form-select'}),
            'client': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        lead = cleaned_data.get('lead')
        client = cleaned_data.get('client')
        due_date = cleaned_data.get("due_date")
        due_time = cleaned_data.get("due_time")
        if due_date and due_time:
            # Combine to datetime if both provided (optional, as per your app logic)
            import datetime
            cleaned_data['due_datetime'] = datetime.datetime.combine(due_date, due_time)

        # Ensure not both lead and client are selected
        if lead and client:
            raise forms.ValidationError(
                "A task cannot be related to both a lead and a client simultaneously."
            )

        return cleaned_data


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}),
        }


class TaskEditForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'due_time', 'status', 'priority', 'assigned_to' ]
        widgets = {
            'due_date': forms.DateInput(attrs={
                'type': 'text',
                'class': 'form-control',
                'placeholder': 'dd.mm.yyyy',
                'autocomplete': 'off'
            }),
            'due_time': Time24HourInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }