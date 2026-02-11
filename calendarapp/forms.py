from django import forms
from django.forms.widgets import TimeInput
from .models import Event


class Time24HourInput(TimeInput):
    input_type = 'text'
    format = '%H:%M'

    def __init__(self, attrs=None, format=None):
        default_attrs = {'placeholder': 'HH:MM', 'pattern': '[0-9]{2}:[0-9]{2}'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, format=format or self.format)


class EventForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'text', 'class': 'form-control', 'placeholder': 'dd.mm.yyyy'}),
        required=True
    )
    start_time = forms.TimeField(
        widget=Time24HourInput(attrs={'class': 'form-control'}),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'text', 'class': 'form-control', 'placeholder': 'dd.mm.yyyy'}),
        required=False
    )
    end_time = forms.TimeField(
        widget=Time24HourInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Event
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Combine date and time fields
        import datetime
        start_date = self.cleaned_data.get('start_date')
        start_time = self.cleaned_data.get('start_time')
        end_date = self.cleaned_data.get('end_date')
        end_time = self.cleaned_data.get('end_time')

        if start_date and start_time:
            instance.start = datetime.datetime.combine(start_date, start_time)

        if end_date and end_time:
            instance.end = datetime.datetime.combine(end_date, end_time)
        elif end_date:
            instance.end = datetime.datetime.combine(end_date, datetime.time(23, 59))

        if commit:
            instance.save()
        return instance
