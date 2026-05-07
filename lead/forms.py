from django import forms

from .models import Lead, Comment, LeadFile


class AddLeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ('company', 'first_name', 'last_name', 'title', 'phone', 'mobile',
                  'address', 'zipcode', 'city', 'country', 'email', 'description',
                  'website', 'priority', 'status', 'status_sale')

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name', '').strip()
        last_name = cleaned_data.get('last_name', '').strip()

        if first_name or last_name:
            qs = Lead.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                name = f'{first_name} {last_name}'.strip()
                raise forms.ValidationError(
                    f'A lead named "{name}" already exists in the list.'
                )
        return cleaned_data


class AddCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)

class AddFileForm(forms.ModelForm):
    class Meta:
        model = LeadFile
        fields = ('file',)
