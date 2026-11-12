from django import forms
from django.core.validators import validate_email
from email.utils import getaddresses

from client.models import Client
from lead.models import Lead
from .models import MailAccount


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


# Server presets for common providers (filled into the form by JavaScript, the user can still change them)
MAIL_PROVIDERS = {
    'gmail': {'label': 'Gmail / Google Workspace', 'imap_host': 'imap.gmail.com', 'imap_port': 993,
              'smtp_host': 'smtp.gmail.com', 'smtp_port': 587, 'smtp_security': 'starttls',
              'hint': 'Use a Google App Password (Google account -> Security -> 2-Step Verification -> App passwords).'},
    'outlook': {'label': 'Outlook / Microsoft 365', 'imap_host': 'outlook.office365.com', 'imap_port': 993,
                'smtp_host': 'smtp.office365.com', 'smtp_port': 587, 'smtp_security': 'starttls',
                'hint': 'IMAP/SMTP with a password must be allowed for your Microsoft account.'},
    'yahoo': {'label': 'Yahoo Mail', 'imap_host': 'imap.mail.yahoo.com', 'imap_port': 993,
              'smtp_host': 'smtp.mail.yahoo.com', 'smtp_port': 465, 'smtp_security': 'ssl',
              'hint': 'Use an app password generated in your Yahoo account security settings.'},
    'icloud': {'label': 'iCloud Mail', 'imap_host': 'imap.mail.me.com', 'imap_port': 993,
               'smtp_host': 'smtp.mail.me.com', 'smtp_port': 587, 'smtp_security': 'starttls',
               'hint': 'Use an app-specific password from appleid.apple.com.'},
    'seznam': {'label': 'Seznam.cz', 'imap_host': 'imap.seznam.cz', 'imap_port': 993,
               'smtp_host': 'smtp.seznam.cz', 'smtp_port': 465, 'smtp_security': 'ssl',
               'hint': 'Enable "access via IMAP/SMTP" in the Seznam Email settings.'},
}


class MailAccountForm(forms.ModelForm):
    provider = forms.ChoiceField(
        required=False,
        choices=[('', 'Custom / other provider')] + [(key, p['label']) for key, p in MAIL_PROVIDERS.items()],
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Choose your provider to fill in the server settings automatically.',
    )
    password = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text='For Gmail, Yahoo or iCloud use an app password.',
    )
    test_connection = forms.BooleanField(
        required=False, initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Test the connection before saving',
    )

    class Meta:
        model = MailAccount
        fields = ('email_address', 'display_name', 'username', 'imap_host', 'imap_port',
                  'smtp_host', 'smtp_port', 'smtp_security')
        labels = {
            'email_address': 'Email address',
            'display_name': 'Sender name',
            'username': 'Login name',
            'imap_host': 'IMAP server (incoming)',
            'imap_port': 'IMAP port',
            'smtp_host': 'SMTP server (outgoing)',
            'smtp_port': 'SMTP port',
            'smtp_security': 'SMTP security',
        }
        help_texts = {
            'display_name': 'Shown to recipients, e.g. "Jane Doe". Empty = your CRM name.',
            'username': 'Leave empty if it is the same as the email address.',
            'imap_port': 'IMAP always uses SSL, usually port 993.',
        }
        widgets = {
            'email_address': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'you@example.com'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'imap_host': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'imap.example.com'}),
            'imap_port': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 65535}),
            'smtp_host': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'smtp.example.com'}),
            'smtp_port': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 65535}),
            'smtp_security': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        has_password = bool(self.instance.pk and self.instance.password)
        if has_password:
            self.fields['password'].widget.attrs['placeholder'] = '•••••••• (leave empty to keep the saved password)'
        if not self.is_bound:
            for key, preset in MAIL_PROVIDERS.items():
                if self.instance.imap_host == preset['imap_host']:
                    self.initial['provider'] = key
        self._has_password = has_password

    def clean_imap_port(self):
        return self._clean_port('imap_port')

    def clean_smtp_port(self):
        return self._clean_port('smtp_port')

    def _clean_port(self, name):
        port = self.cleaned_data[name]
        if not 1 <= port <= 65535:
            raise forms.ValidationError('Enter a port between 1 and 65535.')
        return port

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password') or ''
        # Keep the stored password unless a new one is entered - but a new mailbox always needs one
        mailbox_changed = self.instance.pk and any(f in self.changed_data for f in ('email_address', 'username', 'imap_host', 'smtp_host'))
        if not password:
            if not self._has_password:
                self.add_error('password', 'Enter the password for your mailbox.')
            elif mailbox_changed:
                self.add_error('password', 'Enter the password again when changing the mailbox or servers.')
            else:
                password = self.instance.password
        cleaned['password'] = password
        return cleaned
