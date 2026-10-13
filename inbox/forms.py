from django import forms
from django.core.validators import validate_email
from email.utils import getaddresses

from client.models import Client
from lead.models import Lead


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput(attrs={'class': 'form-control'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(d, initial) for d in data]
        return [single_clean(data, initial)] if data else []


def _validate_address_list(value):
    addresses = [a for _, a in getaddresses([value]) if a]
    for address in addresses:
        validate_email(address)
    return addresses


class ComposeEmailForm(forms.Form):
    to = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'recipient@example.com, another@example.com'})
    )
    cc = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cc (optional)'})
    )
    subject = forms.CharField(
        max_length=998,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'})
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 12, 'placeholder': 'Write your message...'})
    )
    attachments = MultipleFileField(required=False)

    def clean_to(self):
        value = self.cleaned_data['to']
        if not _validate_address_list(value):
            raise forms.ValidationError('Enter at least one recipient.')
        return value

    def clean_cc(self):
        value = self.cleaned_data['cc']
        _validate_address_list(value)
        return value


class LinkContactForm(forms.Form):
    client = forms.ModelChoiceField(queryset=Client.objects.none(), required=False,
                                    widget=forms.Select(attrs={'class': 'form-select form-select-sm'}))
    lead = forms.ModelChoiceField(queryset=Lead.objects.none(), required=False,
                                  widget=forms.Select(attrs={'class': 'form-select form-select-sm'}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].queryset = Client.objects.filter(created_by=user)
        self.fields['lead'].queryset = Lead.objects.filter(created_by=user)
